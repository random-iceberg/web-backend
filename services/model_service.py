import logging
import os
import uuid

import httpx
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from db import schemas as db
from models.schemas import (
    DeleteResponse,
    ModelCreate,
    ModelResponse,
    TrainingResponse,
)

logger = logging.getLogger(__name__)


async def get_all_models(
    async_session: async_sessionmaker[AsyncSession],
) -> list[ModelResponse]:
    """
    Retrieves all models from the database.

    Returns:
        List[ModelResponse]: List of all model objects
    """
    async with async_session() as session:
        stmt = (
            select(db.Model)
            .order_by(desc(db.Model.created_at))
            .options(selectinload(db.Model.features))
        )
        result = await session.scalars(stmt)

        return [
            ModelResponse(
                id=model.uuid,
                algorithm=model.algorithm,
                name=model.name,
                features=list(map(lambda x: x.name, model.features)),
                accuracy=model.accuracy,
                created_at=model.created_at,
            )
            for model in result
        ]


async def start_model_training(
    async_session: async_sessionmaker[AsyncSession],
    model_data: ModelCreate,
    background_tasks: BackgroundTasks,
) -> TrainingResponse:
    """
    Initiates the training of a new model in the background.

    Args:
        async_session: Database session factory
        model_data: Model configuration
        background_tasks: FastAPI background tasks handler

    Returns:
        TrainingResponse: Object with job information
    """
    # Validate model data
    if not model_data.features:
        raise ValueError("At least one feature must be selected")

    # Generate a unique ID for the model and job
    model_id = str(uuid.uuid4())
    job_id = f"train_{model_id}"

    # Store initial model information in database
    async with async_session() as session:
        stmt = select(db.Feature).where(db.Feature.name.in_(model_data.features))
        features = await session.scalars(stmt)

        session.add(
            db.Model(
                uuid=model_id,
                algorithm=model_data.algorithm,
                name=model_data.name,
                features=features.all(),
            )
        )
        await session.commit()

    # Start the training process in the background
    background_tasks.add_task(_train_model_task, async_session, model_id, model_data)

    return TrainingResponse(
        job_id=job_id,
        status="training_started",
        message=f"Training started for model '{model_data.name}' using {model_data.algorithm}",
    )


async def delete_model(
    async_session: async_sessionmaker[AsyncSession], model_id: str
) -> DeleteResponse:
    """
    Deletes a model from the database.

    Args:
        async_session: Database session factory
        model_id: ID of the model to delete

    Returns:
        DeleteResponse: Status and message
    """
    async with async_session() as session:
        # Check if model exists
        stmt = select(db.Model).where(db.Model.uuid == model_id)
        result = await session.scalars(stmt)
        model = result.one_or_none()

        if model is None:
            raise ValueError(f"Model with ID {model_id} not found")

        # Delete the model from database
        await session.delete(model)
        await session.commit()

    # TODO: Implement cleanup of model files from storage if needed

    return DeleteResponse(
        status="success",
        message=f"Model '{model.name}' (ID: {model_id}) successfully deleted",
    )


async def _train_model_task(
    async_session: async_sessionmaker[AsyncSession],
    model_id: str,
    model_data: ModelCreate,
) -> None:
    """
    Background task to train the model.

    Args:
        async_session: Database session factory
        model_id: ID of the model to train
        model_data: Model configuration
    """
    logger.info(f"Starting training for model {model_id} ({model_data.name})")
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    try:
        async with httpx.AsyncClient() as client:
            # Health check for the model service
            await _check_model_service_health(client, MODEL_SERVICE_URL, model_id)

            # Prepare and send training request
            training_payload = _prepare_training_payload(model_data)

            logger.info(
                f"Sending training request to model service for model {model_id} "
                f"with payload: {training_payload}"
            )

            response = await client.post(
                f"{MODEL_SERVICE_URL}/models/train",
                json=training_payload,
                timeout=300.0,  # 5 min timeout for training
            )
            response.raise_for_status()

            # Process training results
            await _process_training_results(async_session, model_id, response.json())

    except httpx.HTTPStatusError as exc:
        logger.error(
            f"HTTP error during model training for {model_id}: "
            f"{exc.response.status_code} - {exc.response.text}"
        )
        await _update_model_status(async_session, model_id, "training_failed")
    except httpx.RequestError as exc:
        logger.error(f"Request error during model training for {model_id}: {exc}")
        await _update_model_status(async_session, model_id, "training_failed")
    except Exception as e:
        logger.error(f"Unexpected error training model {model_id}: {str(e)}")
        await _update_model_status(async_session, model_id, "training_failed")


async def _check_model_service_health(
    client: httpx.AsyncClient, service_url: str, model_id: str
) -> None:
    """Check if model service is healthy."""
    try:
        health_response = await client.get(f"{service_url}/health", timeout=5.0)
        health_response.raise_for_status()
        logger.info(f"Model service health check successful for model {model_id}")
    except httpx.RequestError as exc:
        logger.error(f"Model service health check failed for model {model_id}: {exc}")
        raise HTTPException(
            status_code=503, detail=f"Model service is unavailable: {exc}"
        )


def _prepare_training_payload(model_data: ModelCreate) -> dict:
    """Prepare training payload for model service."""
    # Map frontend algorithm names to model service codes
    ALGORITHM_MAP = {
        "Random Forest": "rf",
        "SVM": "svm",
        "Decision Tree": "dt",
        "Logistic Regression": "lr",
    }

    # Map to model service format
    algo_name = ALGORITHM_MAP.get(model_data.algorithm, "rf")

    return {
        "algo": {"name": algo_name},
        "features": model_data.features,
    }


async def _process_training_results(
    async_session: async_sessionmaker[AsyncSession],
    model_id: str,
    training_result: dict,
) -> None:
    """Process and store training results."""
    model_info = training_result.get("info", {})
    accuracy = model_info.get("accuracy")
    features_used = model_info.get("features", [])

    async with async_session() as session:
        stmt = select(db.Model).where(db.Model.uuid == model_id)
        result = await session.scalars(stmt)
        model_db_instance = result.one_or_none()

        if model_db_instance:
            if accuracy is not None:
                model_db_instance.accuracy = accuracy
                logger.info(
                    f"Training completed for model {model_id} with accuracy: {accuracy}"
                )
            else:
                logger.warning(
                    f"Model service did not return accuracy for model {model_id}. "
                    f"Response: {training_result}"
                )

            if features_used:
                # Feature Featching
                existing_features_stmt = select(db.Feature).where(
                    db.Feature.name.in_(features_used)
                )
                existing_features = (await session.scalars(existing_features_stmt)).all()
                existing_feature_names = {f.name for f in existing_features}

                new_features = [
                    db.Feature(name=f_name)
                    for f_name in features_used
                    if f_name not in existing_feature_names
                ]
                session.add_all(new_features)
                await session.flush()

                # Feature Linking
                model_db_instance.features = existing_features + new_features
                logger.info(
                    f"Updated features for model {model_id}: {features_used}"
                )
            else:
                logger.warning(
                    f"Model service did not return features for model {model_id}. "
                    f"Response: {training_result}"
                )

            await session.commit()
        else:
            logger.error(f"Model {model_id} not found in DB after training")


async def _update_model_status(
    async_session: async_sessionmaker[AsyncSession], model_id: str, status: str
) -> None:
    """Update model status in database."""
    async with async_session() as session:
        stmt = select(db.Model).where(db.Model.uuid == model_id)
        result = await session.scalars(stmt)
        model = result.one_or_none()

        if model:
            # Add a status field to model if needed
            # model.status = status
            await session.commit()
            logger.info(f"Updated model {model_id} status to: {status}")
