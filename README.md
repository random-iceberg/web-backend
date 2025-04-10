# Backend Service for Titanic Survivor Prediction Application

This FastAPI-based backend service handles the business logic, API endpoints, and communication with the ML model service for real-time survival predictions. It is fully production-ready and containerized for seamless deployment.

## Project Structure

The backend service is built with FastAPI to handle business logic and API endpoints. Its structure promotes clarity and ease of testing:

```
app/backend/
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies and environment settings
├── README.md              # Backend service documentation
├── routers/               # Modular API route definitions
├── models/                # Data models and schemas
├── services/              # Business logic and integration layers (e.g., ML interfacing, authentication)
└── tests/                 # Unit and integration tests
```

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

The backend service is a critical component that:
- Processes user requests for survival predictions.
- Securely interfaces with the model service to deliver real-time results.
- Exposes administrative endpoints for model management (listing, training, deletion).
- Integrates with the authentication and data storage layer provided by Supabase.

## Features

- **RESTful API with OpenAPI Documentation**: Accessible via Swagger UI.
- **Asynchronous Processing**: Optimized for performance using FastAPI's asynchronous capabilities.
- **Integrated ML Inference**: Communicates with the dedicated model service.
- **Zero Local Configuration**: Pre-configured to run via Docker Compose.
- **Robust Security**: Secure endpoints with proper authentication.

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
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```
  This will start the FastAPI server with auto-reload for development.

- **Code Quality Tools:**
  - Run `flake8` for linting.
  - Run `black` for code formatting.

## Testing

Run the tests using:
```bash
pytest
```
Ensure that both unit and integration tests pass before merging changes.

## Deployment

This service is built for production deployment using Docker. To build and run with Docker Compose, execute:
```bash
docker-compose up --build -d
```

## Troubleshooting

- **Service Logs:**
  ```bash
  docker-compose logs backend
  ```
- **Service Status:**
  ```bash
  docker-compose ps
  ```
- **Network Issues:**
  Verify that dependent services (Model Service, Supabase) are running.

## Documentation

Detailed API and architectural documentation is available via the integrated Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs) and is complemented by the [Project Charter](https://mygit.th-deg.de/schober-teaching/student-projects/ain-23-software-engineering/ss-25/Random_Iceberg/docker-compose/-/wikis/home) in the docs submodule.
