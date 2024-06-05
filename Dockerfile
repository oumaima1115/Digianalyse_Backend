FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /code

# First, install system dependencies
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt && \
    pip install --no-cache-dir protobuf==3.15.3
    
# Copy the rest of the application code into the container
COPY . .

# Back to the primary working directory
WORKDIR /code