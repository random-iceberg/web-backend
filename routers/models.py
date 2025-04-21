from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from models.schemas import ModelCreate, ModelResponse, TrainingResponse, DeleteResponse
from services.model_service import get_all_models, start_model_training, delete_model

router = APIRouter()

@router.get("/", response_model=List[ModelResponse], summary="List all trained models")
async def list_models():
    """
    Retrieves a list of all available trained models.
    
    Returns:
        List[ModelResponse]: A list of model objects containing id, algorithm, name, 
                            created_at, features, and accuracy.
    """
    try:
        models = await get_all_models()
        return models
    except Exception as exc:
        # TODO: Add proper logging
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(exc)}")

@router.post("/train", response_model=TrainingResponse, summary="Train a new model")
async def train_model(model_data: ModelCreate, background_tasks: BackgroundTasks):
    """
    Initiates the training of a new ML model.
    
    Args:
        model_data (ModelCreate): The model configuration including algorithm, name, and features
        background_tasks (BackgroundTasks): FastAPI background tasks handler
    
    Returns:
        TrainingResponse: Object containing job_id, status, and message
    """
    try:
        # Start training in the background to avoid blocking
        response = await start_model_training(model_data, background_tasks)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        # TODO: Add proper logging
        raise HTTPException(status_code=500, detail=f"Failed to start model training: {str(exc)}")

@router.delete("/{model_id}", response_model=DeleteResponse, summary="Delete a model")
async def remove_model(model_id: str):
    """
    Removes a specific model by ID.
    
    Args:
        model_id (str): Unique identifier of the model to delete
    
    Returns:
        DeleteResponse: Object containing status and message
    """
    try:
        response = await delete_model(model_id)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        # TODO: Add proper logging
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(exc)}")