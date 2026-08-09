FROM python:3.12.9-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system commerce && adduser --system --ingroup commerce commerce

COPY pyproject.toml alembic.ini ./
COPY alembic ./alembic
COPY apps ./apps
COPY packages ./packages

RUN pip install --upgrade pip==26.2.1 && pip install .

USER commerce

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
