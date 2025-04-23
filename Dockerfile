FROM python:3.13 AS base

WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY . .
CMD ["python", "entry.py"]

FROM base AS dev

FROM base AS prod
ENV ENVIRONMENT=production
