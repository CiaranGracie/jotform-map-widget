FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.3

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "3600", "--workers", "2", "app:app"]
