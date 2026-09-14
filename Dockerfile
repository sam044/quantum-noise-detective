FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/src \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 QND_PUBLIC=1 \
    QND_DATA_DIR=/data QND_MODELS_DIR=/app/artifacts/models
COPY requirements-lock-linux-serving.txt .
RUN pip install --no-cache-dir -r requirements-lock-linux-serving.txt
COPY src/qnd/*.py ./src/qnd/
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit
COPY scripts/serve.py ./scripts/serve.py
COPY artifacts ./artifacts
EXPOSE 8080
CMD ["python", "scripts/serve.py"]
