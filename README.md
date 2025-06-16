# Backend API Service

FastAPI-based backend service for the Titanic Survivor Prediction Application.

## 🚀 Quick Start (Zero Configuration)

```bash
# From the project root directory
docker compose -f 'compose/compose.dev.yaml' up -d --build

# Access Swagger UI
open http://localhost:8000/docs
```

No setup needed! The service starts with all dependencies configured.

## 📋 Features

- **RESTful API** with automatic OpenAPI/Swagger documentation
- **JWT Authentication** with role-based access control
- **Async PostgreSQL** integration with SQLAlchemy
- **Structured logging** and error handling
- **Health checks** and monitoring endpoints
- **Auto-reload** in development mode

## 🏗️ API Documentation

### Interactive API Explorer
Access the Swagger UI at: **http://localhost:8000/docs**

### Main Endpoints

#### Public
- `GET /health` - Service health check
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication (returns JWT token)

#### Protected (Requires Authentication)
- `POST /predict` - Get survival prediction
- `GET /predict/history` - View last 10 predictions

#### Admin Only
- `GET /models` - List available ML models
- `POST /models/train` - Train new model
- `DELETE /models/{id}` - Delete specific model

## 🛠️ Development Workflow

## 🧪 Testing

```bash
cd app/backend

# Install dependencies (if not already done)
uv sync --no-cache --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-report=html

# Linting and formatting check
uv run ruff check
uv run ruff format --check

# Auto-fix formatting
uv run ruff format
```

## 📁 Project Structure

```
backend/
├── main.py              # Application entry point
├── routers/             # API route handlers
│   ├── auth.py         # Authentication endpoints
│   ├── models.py       # Model management
│   └── prediction.py   # Prediction endpoints
├── services/           # Business logic
│   ├── prediction_service.py
│   ├── model_service.py
│   └── user_service.py
├── db/                 # Database layer
│   ├── schemas.py      # SQLAlchemy models
│   └── helpers.py      # DB utilities
├── models/             # Pydantic schemas
└── tests/              # Test suite
```

## 🔧 Configuration

The service is pre-configured in Docker Compose. For local development:

| Variable | Description | Docker Default |
|----------|-------------|----------------|
| `DB_USER` | Database user | `backend` |
| `DB_DATABASE` | Database name | `backend` |
| `DB_ADDRESS` | Database host | `postgres` |
| `DB_PASSWORD` | Database password | Set in compose |
| `JWT_SECRET_KEY` | JWT signing key | Set in compose |
| `MODEL_SERVICE_URL` | Model service URL | `http://model:8000` |
| `ALLOWED_ORIGINS` | CORS origins | `*` |

## 📊 Database Management

Use pgAdmin for database exploration:
- URL: http://localhost:5050
- Email: `team@random.iceberg`
- Password: `Cheezus123`

### Database Schema
- `users` - User accounts and authentication
- `prediction` - Prediction history
- `model` - Trained model metadata
- `feature` - Available ML features

## 🔍 Testing the API

### Using Swagger UI
1. Go to http://localhost:8000/docs
2. Try the `/health` endpoint first
3. Use `/auth/signup` to create a user
4. Use `/auth/login` to get a JWT token
5. Click "Authorize" and paste the token
6. Test protected endpoints

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## 🐳 CI/CD Pipeline

The GitLab CI pipeline automatically:
- Runs tests on every commit
- Checks code formatting with ruff
- Builds Docker image
- Pushes to registry (for main/dev branches)

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Project Requirements](../../docs/Project-Requirements.md)
- [API Design Patterns](https://docs.anthropic.com/patterns/api-design)
