# Backend Service for Titanic Survivor Prediction Application

This service is built using FastAPI to handle business logic, manage API endpoints, and coordinate ML model inference and administrative tasks for the Titanic Survivor Prediction Application. All configuration is pre-integrated so that no manual environment variable setup is needed. The backend is production-ready and fully documented.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

## Overview

The backend service is the cornerstone of the Titanic Survivor Prediction Application. It exposes a robust RESTful API to:
- Process user requests for survival prediction.
- Interface securely with the dedicated model service for ML inference.
- Provide administrative endpoints for model management (listing, training, deletion).
- Integrate seamlessly with the authentication and data persistence layer.

This service leverages asynchronous processing for optimal performance and is designed to operate within a containerized Docker environment, ensuring scalability and high availability.

## Features

- **RESTful API with OpenAPI Specification:**  
  Self-documented endpoints accessible via Swagger UI.
- **Fast and Asynchronous:**  
  Utilizes FastAPI’s asynchronous capabilities for swift request processing.
- **Integrated ML Model Inference:**  
  Interfaces with the dedicated model service to deliver real-time predictions.
- **Administrative Endpoints:**  
  Supports secure model management (viewing, training, deletion) as per the Project Charter.
- **Zero Local Configuration:**  
  The service is fully configured to run out of the box using Docker Compose, eliminating manual environment variable setups.
- **Robust Security:**  
  Secured endpoints ensure that only authenticated users gain access to extended functionalities.

## Getting Started

1. **Clone the Repository:**

   ```bash
   git clone https://your.git.repo/app/backend.git
   cd app/backend
   ```

2. **Create a Virtual Environment and Install Dependencies:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Development

- **Run Locally:**  
  Use the following command to start the FastAPI server with auto-reload enabled for development:
  
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

- **Code Quality:**  
  - **Linting:** Run `flake8` to identify and fix styling issues.
  - **Formatting:** Use `black` to enforce consistent code formatting.

## Testing

- **Unit and Integration Tests:**  
  The backend is covered by comprehensive tests. Run the tests using:
  
  ```bash
  pytest
  ```

## Deployment

This service is designed for production deployment using Docker. All configuration is embedded in the Docker setup.

- **Build and Run with Docker Compose:**  
  From the root of the repository, start all services with:
  
  ```bash
  docker-compose up --build -d
  ```
  
  This command builds and launches the backend along with the frontend, model service, and Supabase instance.

## Troubleshooting

- **Common Issues:**
  - Check service logs via Docker for any errors:
    
    ```bash
    docker-compose logs backend
    ```
    
  - Ensure that dependent services (Model and Supabase) are running successfully.
  - Verify that the Docker network is routing requests correctly by checking the container statuses:
    
    ```bash
    docker-compose ps
    ```
    
- **Documentation:**  
  Detailed API and architectural documentation are available via the integrated Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

## Documentation

For further details on API endpoints, administrative interfaces, and internal architecture, please refer to the project documentation in the `/docs` submodule. The documentation is maintained to align with the latest updates from the Project Charter.

---

*This backend is part of a larger, fully orchestrated system designed to demonstrate modern agile practices, robust scalability, and a seamless user experience in Titanic survival prediction.*
