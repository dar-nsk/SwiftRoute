FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data
RUN python scripts/train_model.py
# Graph download is optional — routing uses OSRM (global), graph only needed for local VRP.
# Try to download but don't fail the build if Overpass is rate-limited.
RUN python scripts/download_graph.py || echo "Graph download skipped (rate-limited). Will retry on first request."
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
