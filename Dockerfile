FROM ghcr.io/astral-sh/uv:0.7.4-python3.13-bookworm-slim AS base

RUN apt-get update && apt-get install -y curl

WORKDIR /app

COPY ./pyproject.toml .
RUN uv sync --no-cache --no-install-project
COPY . .

FROM base AS dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
ENV ENVIRONMENT=production
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
