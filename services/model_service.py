import logging
import os
import time
import uuid
from datetime import datetime

import httpx
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from tenacity import retry, stop_after_attempt, wait_exponential

from db import schemas as db
from models.schemas import (
    DeleteResponse,
    ModelCreate,
    ModelResponse,
    TrainingResponse,
)

logger = logging.getLogger(__name__)

MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

# In-memory cache for models
_model_cache = {"data": None, "timestamp": 0}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes

# Map model service algorithm codes to human-readable names
ALGORITHM_NAME_MAP = {
    "rf": "Random Forest",
    "svm": "SVM",
    "dt": "Decision Tree",
    "lr": "Logistic Regression",
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _fetch_models_from_model_service() -> list[ModelResponse]:
    """
    Fetches models from the external model service with retry logic.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODEL_SERVICE_URL}/models/", timeout=10.0)
        response.raise_for_status()
        model_service_models = response.json()
        return [
            ModelResponse(
                id=model["id"],
                algorithm=ALGORITHM_NAME_MAP.get(
                    model["params"]["algo"]["name"], model["params"]["algo"]["name"]
                ),
                name=model["id"],  # Model service doesn't have a 'name' field directly
                features=model["params"]["features"],
                accuracy=model["info"].get("accuracy"),
                created_at=(
                    datetime.fromisoformat(model["info"]["created_at"])
                    if model["info"].get("created_at")
                    else None
                ),
            )
            for model in model_service_models
        ]


async def get_all_models(
    async_session: async_sessionmaker[AsyncSession],
) -> list[ModelResponse]:
    """
    Retrieves all models by merging results from the database and the model service.

    Returns:
        List[ModelResponse]: List of all model objects
    """
    current_time = time.time()
    if _model_cache["data"] and (
        current_time - _model_cache["timestamp"] < CACHE_EXPIRY_SECONDS
    ):
        logger.info("Returning models from cache.")
        return _model_cache["data"]

    db_models: dict[str, ModelResponse] = {}
    async with async_session() as session:
        stmt = (
            select(db.Model)
            .order_by(desc(db.Model.created_at))
            .options(selectinload(db.Model.features))
        )
        result = await session.scalars(stmt)
        for model in result:
            db_models[model.uuid] = ModelResponse(
                id=model.uuid,
                algorithm=ALGORITHM_NAME_MAP.get(model.algorithm, model.algorithm),
                name=model.name,
                features=list(map(lambda x: x.name, model.features)),
                accuracy=model.accuracy,
                created_at=model.created_at,
                status=model.status,
            )

    model_service_models: list[ModelResponse] = []
    try:
        model_service_models = await _fetch_models_from_model_service()
    except httpx.RequestError as exc:
        logger.warning(f"Model service is unavailable, returning only DB models: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.warning(
            f"Model service returned an error, returning only DB models: "
            f"{exc.response.status_code} - {exc.response.text}"
        )
    except Exception as exc:
        logger.error(f"Unexpected error fetching models from model service: {exc}")

    # Merge results: prioritize DB models if ID exists in both
    merged_models: dict[str, ModelResponse] = {}
    for model in model_service_models:
        merged_models[model.id] = model

    for model_id, model_data in db_models.items():
        merged_models[model_id] = model_data

    # Sort models by created_at, if available, otherwise by ID
    sorted_models = sorted(
        merged_models.values(),
        key=lambda m: m.created_at if m.created_at else datetime.min,
        reverse=True,
    )

    _model_cache["data"] = sorted_models
    _model_cache["timestamp"] = current_time
    logger.info("Models fetched and cached.")

    return sorted_models


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
                status="training_in_progress",
            )
        )
        await session.commit()

    # Invalidate cache after training a new model
    _model_cache["data"] = None
    _model_cache["timestamp"] = 0
    logger.info("Model cache invalidated due to new model training.")

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
    Deletes a model from the database and attempts to delete from model service.

    Args:
        async_session: Database session factory
        model_id: ID of the model to delete

    Returns:
        DeleteResponse: Status and message
    """
    async with async_session() as session:
        # Check if model exists in DB
        stmt = select(db.Model).where(db.Model.uuid == model_id)
        result = await session.scalars(stmt)
        model = result.one_or_none()

        if model is None:
            # If not in DB, check if it's a default model from the model service
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{MODEL_SERVICE_URL}/models/{model_id}", timeout=5.0
                    )
                    response.raise_for_status()
                    model_service_model = response.json()
                    if not model_service_model.get("removable", True):
                        raise ValueError(f"Model with ID {model_id} is not removable")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ValueError(f"Model with ID {model_id} not found")
                else:
                    logger.error(f"Error checking model service for {model_id}: {exc}")
                    raise HTTPException(
                        status_code=500, detail="Failed to check model service"
                    )
            except httpx.RequestError as exc:
                logger.warning(
                    f"Could not connect to model service to verify model {model_id}: {exc}"
                )
                raise HTTPException(status_code=503, detail="Model service unavailable")
            except Exception as exc:
                logger.error(f"Unexpected error checking model service: {exc}")
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                )

        # Delete from database if it exists
        if model:
            await session.delete(model)
            await session.commit()
            logger.info(f"Model '{model.name}' (ID: {model_id}) deleted from DB")

        # Attempt to delete from model service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{MODEL_SERVICE_URL}/models/{model_id}", timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Model {model_id} deleted from model service")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.info(
                    f"Model {model_id} not found in model service (already deleted or never existed there)"
                )
            elif exc.response.status_code == 403:
                logger.warning(f"Model {model_id} is not removable from model service")
            else:
                logger.error(
                    f"HTTP error deleting model {model_id} from model service: "
                    f"{exc.response.status_code} - {exc.response.text}"
                )
                # Do not re-raise, as DB deletion might have succeeded
        except httpx.RequestError as exc:
            logger.warning(
                f"Could not connect to model service to delete model {model_id}: {exc}"
            )
            # Do not re-raise, as DB deletion might have succeeded
        except Exception as exc:
            logger.error(
                f"Unexpected error deleting model {model_id} from model service: {exc}"
            )
            # Do not re-raise

    # Invalidate cache after deleting a model
    _model_cache["data"] = None
    _model_cache["timestamp"] = 0
    logger.info("Model cache invalidated due to model deletion.")

    return DeleteResponse(
        status="success",
        message=f"Model (ID: {model_id}) successfully deleted (if it existed)",
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
    # MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000") # Already defined globally

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

    ALGORITHM_MAP = {
        "Random Forest": "rf",
        "SVM": "svm",
        "Decision Tree": "dt",
        "Logistic Regression": "lr",
    }

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
    model_service_id = training_result["id"]
    accuracy = training_result["info"]["accuracy"]
    features_used = training_result["params"]["features"]

    async with async_session() as session:
        stmt = select(db.Model).where(db.Model.uuid == model_id)
        result = await session.scalars(stmt)
        model_db_instance = result.one_or_none()

        if model_db_instance:
            model_db_instance.uuid = model_service_id

            if accuracy is not None:
                model_db_instance.accuracy = accuracy
                logger.info(
                    f"Training completed for model {model_service_id} with accuracy: {accuracy}"
                )
            else:
                logger.warning(
                    f"Model service did not return accuracy for model {model_service_id}. "
                    f"Response: {training_result}"
                )

            if features_used:
                # Feature Fetching
                existing_features_stmt = select(db.Feature).where(
                    db.Feature.name.in_(features_used)
                )
                existing_features = (
                    await session.scalars(existing_features_stmt)
                ).all()
                existing_feature_names = {f.name for f in existing_features}

                new_features = [
                    db.Feature(name=f_name)
                    for f_name in features_used
                    if f_name not in existing_feature_names
                ]
                session.add_all(new_features)
                await session.flush()

                # Feature Linking
                # Ensure the relationship is loaded before modification
                await session.refresh(model_db_instance, attribute_names=["features"])
                model_db_instance.features = existing_features + new_features
                logger.info(
                    f"Updated features for model {model_service_id}: {features_used}"
                )
            else:
                logger.warning(
                    f"Model service did not return features for model {model_service_id}. "
                    f"Response: {training_result}"
                )
            model_db_instance.status = "ready"
            await session.commit()
            # Invalidate cache after training completion
            _model_cache["data"] = None
            _model_cache["timestamp"] = 0
            logger.info("Model cache invalidated due to training completion.")
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
            model.status = status
            await session.commit()
            logger.info(f"Updated model {model_id} status to: {status}")
            _model_cache["data"] = None
            _model_cache["timestamp"] = 0
            logger.info("Model cache invalidated due to status update.")
