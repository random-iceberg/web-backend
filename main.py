from fastapi import FastAPI
from routers import prediction

app = FastAPI(
    title="Titanic Survivor Prediction Backend Web",
    description="API for predicting Titanic passenger survival using a model-based inference service.",
    version="1.0.0"
)

# Include the prediction routes at the "/predict" path
app.include_router(prediction.router, prefix="/predict")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)
