FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir fastapi==0.115.8 uvicorn[standard]==0.34.0 crawlee==0.6.12 beautifulsoup4==4.12.3

COPY app.py /app/app.py

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
