# ============================
# Base image
# ============================
FROM python:3.10-slim

# Avoid Python writing .pyc files and enable stdout flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# ============================
# System dependencies
# ============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Install Python deps early (cache)
# ============================
COPY backend/requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# Copy project
# ============================
COPY backend/ .
COPY db_mongo/ /db_mongo/

# ============================
# Expose & start server
# ============================
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
