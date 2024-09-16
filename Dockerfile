# Use Python 3.9 slim-buster as the base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /code

# Install system dependencies (git in this case)
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Downgrade pip to avoid celery installation issues
RUN pip install pip==23.2.1

# Copy requirements.txt first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python dependencies, with no-cache and protobuf installation
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt && \
    pip install --no-cache-dir protobuf==3.15.3

# Copy the rest of the application code into the container
COPY . .

# Set the working directory back to /code (if changed during COPY)
WORKDIR /code
