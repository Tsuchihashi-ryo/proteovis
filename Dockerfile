# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV PORT 8080

# Create and set the working directory
WORKDIR $APP_HOME

# Install system dependencies required for psycopg2 and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the application using Gunicorn
# Using 4 workers, a timeout of 120 seconds, and binding to the port specified by the PORT env var.
# The entrypoint is the 'app' object in the 'main.py' file.
CMD exec gunicorn --workers 4 --timeout 120 --bind :$PORT main:app
