# Simple Dockerfile for sam-backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Default Flask port is 5000
ENV FLASK_APP=app.py
CMD ["python", "app.py"]
