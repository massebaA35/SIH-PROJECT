FROM python:3.12-slim

WORKDIR /app

# System deps: none required beyond what pip needs for the pinned wheels used here
# (fpdf2/scipy ship prebuilt wheels for this base image's platform).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8010

# Seed the database on first boot if it doesn't exist yet, then start the API.
CMD ["sh", "-c", "python -m seed.seed_db && uvicorn app.main:app --host 0.0.0.0 --port 8010"]
