# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the entire repository into the container
COPY . .

# Install Poetry
RUN pip install poetry

# Install project dependencies
RUN poetry install --no-root

# Define the command to run your application
CMD ["python", "lib/fhr/fhr_convert.py"]
