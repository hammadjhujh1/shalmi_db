# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install system dependencies
RUN apt-get update && apt-get install -y libmagic1
# Copy the project files
COPY . /app/

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]