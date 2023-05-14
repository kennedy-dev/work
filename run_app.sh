#!/bin/bash

# Activate the virtual environment
source /app/dias/venv/bin/activate

# Run the Gunicorn server with the specified configuration
gunicorn --config gunicorn.conf app:app
