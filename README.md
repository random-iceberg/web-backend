# Backend Web for Titanic Survivor Prediction Application

## Overview

The Backend Web is a FastAPI-based RESTful API responsible for processing Titanic survival prediction requests. It securely integrates with the ML Model API for real-time inference and handles core business logic, authentication, and middleware integration. Built for production, the service supports asynchronous processing, comprehensive API documentation, and containerized deployment via Docker Compose.

## Features

- **Interactive API Documentation:** Accessible via Swagger UI at `/docs`.
- **Asynchronous Processing:** Utilizes FastAPI’s async framework for high performance.
- **Modular Architecture:** Organized into routers, models, and services to ease maintenance and scalability.
- **Secure ML Integration:** Seamlessly communicates with the dedicated Model API for predictions.
- **Containerized Deployment:** Fully supported via Docker Compose for reproducible production environments.
- **Extensible Design:** Prepared for future enhancements including advanced authentication, logging, and error handling.

## Project Structure

```plaintext
app/backend/
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── README.md              # Backend Web documentation (this file)
├── routers/               # Modular API route definitions (e.g., prediction endpoints)
├── models/                # Data models and request/response schemas
├── services/              # Business logic layers (including ML integration and authentication)
└── tests/                 # Unit and integration tests
```

## Getting Started

### Prerequisites

- Python 3.9.x
- Virtual environment (recommended)
- Docker & Docker Compose (for containerized deployment)

### Setup Instructions

Follow these steps to set up your development environment:

1. **Clone the Repository (with Submodules)**  
   Clone the repository together with all its submodules:
   ```bash
   git clone --recurse-submodules https://mygit.th-deg.de/schober-teaching/student-projects/ain-23-software-engineering/ss-25/Random_Iceberg/web-backend.git
   ```

2. **Enter the Project Directory**  
   Change directory into the Docker Compose folder:
   ```bash
   cd docker-compose
   ```

3. **Checkout the Development Branch**  
   Create and switch to a local branch named `dev` that tracks the remote development branch:
   ```bash
   git checkout -b dev origin/dev
   ```

4. **Update All Submodules**  
   Initialize and update every submodule recursively:
   ```bash
   git submodule update --init --recursive
   ```

5. **Create and Activate a Virtual Environment:**
   (From the appropriate directory, e.g., `app/backend`) activate Python 3.9.x virtual environment
   ```bash
   py -3.9 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

6. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

7. **Run the Application Locally:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Access the API at [http://localhost:8000](http://localhost:8000) and the interactive documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Development & Testing

- **Development:**  
  Use uvicorn with `--reload` to benefit from live code updates.
- **Code Quality:**  
  Maintain standards using linters (e.g., flake8) and formatters (e.g., black). Perform regular code reviews.
- **Testing:**  
  Run tests with:
  ```bash
  pytest
  ```

## Deployment

Deploy the Backend Web along with other components using Docker Compose:
```bash
docker-compose up --build -d
```
This command builds the Docker image and launches the container in an orchestrated environment.

## Troubleshooting

- **View Logs:**
  ```bash
  docker-compose logs backend
  ```
- **Check Container Status:**
  ```bash
  docker-compose ps
  ```

## Documentation & References

For further API specifications, architectural details, and integration guidelines, please refer to the [Project Charter](#) and the additional documentation in the `docs/` submodule.

---

Maintained by **team/random_iceberg**.
