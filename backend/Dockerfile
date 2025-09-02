# Start with an official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy your application code into the container
COPY ./app /app/app

# ADD THIS LINE: Copy the model files
COPY ./outputs /app/outputs

# The command to run your application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]