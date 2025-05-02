import uuid
import logging

import asyncio
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from models.schemas import ModelCreate, ModelResponse, TrainingResponse, DeleteResponse
from db import schemas as db


logger = logging.getLogger(__name__)


async def get_all_models(
    async_session: async_sessionmaker[AsyncSession],
) -> list[ModelResponse]:
    """
    Retrieves all models from the database.

    Returns:
        List[ModelResponse]: List of all model objects
    """
    # TODO: Replace with actual database query
    # SELECT * FROM models ORDER BY created_at DESC

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
    # TODO: Replace with actual database insert
    # INSERT INTO models (id, algorithm, name, features, created_at)
    # VALUES (model_id, model_data.algorithm, model_data.name, model_data.features, NOW())
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
    try:
        logger.info(f"Starting training for model {model_id} ({model_data.name})")

        # TODO: Implement actual model training
        # This would involve making a request to the Model Backend service
        # to train the model with the specified algorithm and features

        # For now, simulate training with a placeholder
        await asyncio.sleep(5)

        # Update model with accuracy
        async with async_session() as session:
            stmt = select(db.Model).where(db.Model.uuid == model_id)
            result = await session.scalars(stmt)
            model = result.one()
            model.accuracy = 0.85  # Placeholder accuracy
            await session.commit()

        logger.info(f"Training completed for model {model_id}")
    except Exception as e:
        logger.error(f"Error training model {model_id}: {str(e)}")
        # Update model with error status if needed
        # TODO: Implement error handling for failed training
