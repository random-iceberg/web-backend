# base
FROM ghcr.io/astral-sh/uv:0.7.20-bookworm-slim AS base

RUN apt-get update && apt-get install -y curl

WORKDIR /app

COPY ./pyproject.toml .
COPY uv.lock .
RUN uv sync --locked --no-cache --no-install-project

# dev
FROM base AS dev

RUN apt-get update && apt-get install -y rsync dos2unix
COPY ./container/dev-entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh
ENTRYPOINT [ "bash", "/entrypoint.sh" ]

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# prod
FROM base AS prod

COPY . .

ENV ENVIRONMENT=production
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
