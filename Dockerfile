FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends swi-prolog \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY rules/ rules/
COPY data/ data/
COPY web/ web/
COPY src/ src/
RUN useradd -m appuser
ENV PYTHONPATH=/app/src
ENV PORT=8080
USER appuser
EXPOSE 8080
# shell-form CMD so $PORT (set by Cloud Run) expands; exec replaces the
# shell so SIGTERM reaches uvicorn directly (clean shutdown, no 10s wait)
CMD exec uvicorn seido.app:app --host 0.0.0.0 --port $PORT
