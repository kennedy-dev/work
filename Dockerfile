# Use the official Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN python -m venv dias
RUN /app/dias/bin/pip install --no-cache-dir --upgrade pip setuptools
RUN /app/dias/bin/pip install --no-cache-dir -r requirements.txt

# Add pip-autoremove and clean up unused dependencies
RUN /app/dias/bin/pip install --no-cache-dir pip-autoremove
RUN /app/dias/bin/pip-autoremove -y

# Copy the application code to the container
COPY . .

# Set the environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8081

# Perform the database migrations
RUN /app/dias/bin/python -m flask db init
RUN /app/dias/bin/python -m flask db migrate
RUN /app/dias/bin/python -m flask db upgrade

# Expose the port that the app will run on
EXPOSE 8081

# Start the application with Gunicorn
CMD ["/app/dias/bin/gunicorn", "-c", "gunicorn.conf.py", "app:app"]
