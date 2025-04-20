from fastapi import FastAPI
from routers import prediction

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    TODO:
      - Initialize middleware (e.g. CORS, logging, error handling).
      - Configure any global settings (database connections, security, etc.).
    """
    app = FastAPI(
        title="Titanic Survivor Prediction Backend",
        description="Production-ready backend API for Titanic survival prediction.",
        version="1.0.0"
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
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
