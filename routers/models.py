import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from dependencies.auth import has_role, get_user_role # Import get_user_role
from models.schemas import (
    DeleteResponse,
    ModelCreate,
    ModelResponse,
    TrainingResponse,
)
from services.model_service import delete_model, get_all_models, start_model_training

logger = logging.getLogger(__name__)
router = APIRouter() # Removed global dependency


@router.get("/", response_model=list[ModelResponse], summary="List all trained models")
async def list_models(
    request: Request,
    role: Annotated[str, Depends(has_role(["anon", "user", "admin"]))] # Allow all roles
):
    """
    Retrieves a list of all available trained models.

    Returns:
        List[ModelResponse]: A list of model objects containing id, algorithm, name,
                            created_at, features, and accuracy.
    """
    try:
        models = await get_all_models(request.state.async_session)
        return models
    except Exception as exc:
        logger.error(f"Failed to retrieve models: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve models: {str(exc)}"
        )


@router.post("/train", response_model=TrainingResponse, summary="Train a new model")
async def train_model(
    model_data: ModelCreate, 
    background_tasks: BackgroundTasks, 
    request: Request,
    role: Annotated[str, Depends(has_role(["admin"]))] # Admin only
):
    """
    Initiates the training of a new ML model.

    Args:
        model_data (ModelCreate): The model configuration including algorithm, name, and features
        background_tasks (BackgroundTasks): FastAPI background tasks handler

    Returns:
        TrainingResponse: Object containing job_id, status, and message
    """
    try:
        response = await start_model_training(
            request.state.async_session, model_data, background_tasks
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to start model training: {str(exc)}"
        )


@router.delete("/{model_id}", response_model=DeleteResponse, summary="Delete a model")
async def remove_model(
    model_id: str, 
    request: Request,
    role: Annotated[str, Depends(has_role(["admin"]))] # Admin only
):
    """
    Removes a specific model by ID.

    Args:
        model_id (str): Unique identifier of the model to delete

    Returns:
        DeleteResponse: Object containing status and message
    """
    try:
        response = await delete_model(request.state.async_session, model_id)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete model: {str(exc)}"
        )
