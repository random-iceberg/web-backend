from os import environ


from fastapi import FastAPI
from routers import prediction

def create_app(root_path: str) -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    TODO:
      - Initialize middleware (e.g. CORS, logging, error handling).
      - Configure any global settings (database connections, security, etc.).
    """
    app = FastAPI(
        title="Titanic Survivor Prediction Backend",
        description="Production-ready backend API for Titanic survival prediction.",
        version="1.0.0",
        root_path=root_path
    )
    include_routers(app)
    return app

def include_routers(app: FastAPI) -> None:
    """
    Include API routers.
    
    TODO:
      - Include additional routers for authentication, administration, health checks, etc.
    """
    app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])

# Instantiate the application
app = create_app(root_path=environ.get("BACKEND_WEB_ROOT", ""))
