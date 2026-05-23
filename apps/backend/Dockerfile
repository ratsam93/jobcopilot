FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml /app/pyproject.toml
COPY requirements.txt /app/requirements.txt
COPY apps /app/apps

RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && pip install -e /app

EXPOSE 8000

CMD ["uvicorn", "apps.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
