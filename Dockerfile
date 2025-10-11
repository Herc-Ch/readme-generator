# ---- Backend: Flask ----
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose Flask port
EXPOSE 5000

# Run your app.py (adjust if you use flask run)
CMD ["python", "app.py"]
