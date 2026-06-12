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
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uvicorn", "seido.app:app", "--host", "0.0.0.0", "--port", "8080"]
