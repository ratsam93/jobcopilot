FROM python:3.11.0-slim
WORKDIR /data/Resume-Matcher
COPY . .
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential python3-dev git && rm -rf /var/lib/apt/lists/*
RUN pip install -U pip setuptools wheel
RUN pip install -r requirements.txt
RUN python run_first.py
ENTRYPOINT [ "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]

EXPOSE 8501
