import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from dependencies.auth import AdminRole, AnyRole
from models.schemas import (
    DeleteResponse,
    ModelCreate,
    ModelResponse,
    TrainingResponse,
)
from services.model_service import delete_model, get_all_models, start_model_training

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ModelResponse], summary="List all trained models")
async def list_models(
    request: Request,
    role: AnyRole,
):
    """
    Retrieves a list of all available trained models.

    Returns:
        List[ModelResponse]: A list of model objects containing id, algorithm, name,
                            created_at, features, and accuracy.
    """
    correlation_id = request.state.correlation_id

    try:
        models = await get_all_models(request.state.async_session)
        if role == "anon":
            # Filter models for anonymous users
            return list(filter(lambda x: not x.is_restricted, models))
        else:
            # Authenticated users see all models, mark others as restricted if not RF/SVM
            return models
    except Exception as exc:
        logger.error(f"Failed to retrieve models: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(exc)}",
            headers={"X-Correlation-ID": correlation_id},
        )


@router.post("/train", response_model=TrainingResponse, summary="Train a new model")
async def train_model(
    model_data: ModelCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    role: AdminRole,
):
    """
    Initiates the training of a new ML model.

    Args:
        model_data (ModelCreate): The model configuration including algorithm, name, and features
        background_tasks (BackgroundTasks): FastAPI background tasks handler

    Returns:
        TrainingResponse: Object containing job_id, status, and message
    """
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        response = await start_model_training(
            request.state.async_session, model_data, background_tasks
        )
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"X-Correlation-ID": correlation_id},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start model training: {str(exc)}",
            headers={"X-Correlation-ID": correlation_id},
        )


@router.delete("/{model_id}", response_model=DeleteResponse, summary="Delete a model")
async def remove_model(
    model_id: str,
    request: Request,
    role: AdminRole,
):
    """
    Removes a specific model by ID.

    Args:
        model_id (str): Unique identifier of the model to delete

    Returns:
        DeleteResponse: Object containing status and message
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    try:
        response = await delete_model(request.state.async_session, model_id)
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
            headers={"X-Correlation-ID": correlation_id},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete model: {str(exc)}",
            headers={"X-Correlation-ID": correlation_id},
        )
