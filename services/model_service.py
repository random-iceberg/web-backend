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
        model_data (ModelCreate): Model configuration
        background_tasks (BackgroundTasks): FastAPI background tasks handler

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
    Deletes a model from the database and removes associated files.

    Args:
        model_id (str): ID of the model to delete

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

    # TODO: Delete model files from storage
    # This would involve removing the saved model file from the Docker volume

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
        model_id (str): ID of the model to train
        model_data (ModelCreate): Model configuration
    """
    logger.info(f"Starting training for model {model_id} ({model_data.name})")
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    try:
        async with httpx.AsyncClient() as client:
            # Health check for the model service
            try:
                health_response = await client.get(
                    f"{MODEL_SERVICE_URL}/health", timeout=5.0
                )
                health_response.raise_for_status()
                logger.info(
                    f"Model service health check successful for model {model_id}"
                )
            except httpx.RequestError as exc:
                logger.error(
                    f"Model service health check failed for model {model_id}: {exc}"
                )
                # Optionally, can add an update model status to 'training_failed_health_check'
                # For now, the training proceeds and potentially fails at the training request. Need Team Lead Input
                raise HTTPException(
                    status_code=503, detail=f"Model service is unavailable: {exc}"
                )

            '''
            Mapping the features to match how it's expected as an input from the model.
            
            Below, the classes that currently clash between the frontend and the model: 
            Model:
            is_alone = "is_alone"
            age_class = "age_class"

            Frontend:
            const AVAILABLE_FEATURES = [
            { id: "sibsp", label: "Siblings/Spouses" },
            { id: "parch", label: "Parents/Children" },
            ];

            Current solution: # TODO: change in frontend or model later.
            - remove the sibsp and parch features from the feature list, 
            - add is_alone as 1, and age_class as 22, in case values must be sent (randomly chosen by shaf).
            '''

            model_data.features = [feat for feat in model_data.features if feat not in {"sibsp", "parch"}]

            # Prepare data for the model training service
            training_payload = {
                "algo": model_data.algorithm,
                "features": model_data.features,
            }

            logger.info(
                f"Sending training request to model service for model {model_id} with payload: {training_payload}"
            )

            # Call the model service to train the model
            response = await client.post(
                f"{MODEL_SERVICE_URL}/models/train", json=training_payload, timeout=300.0
            )  # 5 min timeout for training
            response.raise_for_status()

            training_result = response.json()
            # Model service currently returns {"status": "..."}.
            # Changed to check if Accuracy is added later on, Need Team Lead Input
            accuracy = training_result.get("accuracy")
            model_service_status = training_result.get("status", "unknown")
            logger.info(
                f"Model service response for model {model_id}: status='{model_service_status}', accuracy='{accuracy}'"
            )

            if accuracy is not None:
                # Update model with accuracy from the model service
                async with async_session() as session:
                    stmt = select(db.Model).where(db.Model.uuid == model_id)
                    result = await session.scalars(stmt)
                    model_db_instance = result.one_or_none()
                    if model_db_instance:
                        model_db_instance.accuracy = accuracy
                        await session.commit()
                        logger.info(
                            f"Training completed and accuracy updated for model {model_id}"
                        )
                    else:
                        logger.error(
                            f"Model {model_id} not found in DB after training attempt."
                        )
            else:
                logger.warning(
                    f"Model service did not return accuracy for model {model_id}. Response: {training_result}"
                )

    except httpx.HTTPStatusError as exc:
        logger.error(
            f"HTTP error during model training request for {model_id}: {exc.response.status_code} - {exc.response.text}"
        )
        # TODO: Update model status to 'training_failed' in DB
        # For now, just error logged
    except httpx.RequestError as exc:
        logger.error(f"Request error during model training for {model_id}: {exc}")
        # TODO: Update model status to 'training_failed' in DB
    except Exception as e:
        logger.error(f"Unexpected error training model {model_id}: {str(e)}")
        # TODO: Update model status to 'training_failed' in DB
