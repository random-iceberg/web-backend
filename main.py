from os import environ


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import prediction, models

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

        # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    include_routers(app)
        # Add a root route
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to the Titanic Survivor Prediction API",
            "docs_url": "/docs",
            "available_endpoints": [
                "/models",
                "/models/train",
                "/predict"
            ]
        }
    return app

def include_routers(app: FastAPI) -> None:
    """
    Include API routers.
    
    TODO:
      - Include additional routers for authentication, administration, health checks, etc.
    """
    app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
    app.include_router(models.router, prefix="/models", tags=["Model Management"])

# Instantiate the application
app = create_app(root_path=environ.get("BACKEND_WEB_ROOT", ""))
