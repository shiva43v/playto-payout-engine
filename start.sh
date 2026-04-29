#!/bin/bash

# Change to the backend directory
cd backend || exit

# Start Celery worker in the background (using solo pool to save memory)
celery -A config worker -l info -P solo --concurrency=1 &

# Start Celery beat in the background
celery -A config beat -l info &

# Start the web server in the foreground (limit to 1 worker to save memory)
gunicorn config.wsgi:application --workers 1 --threads 2
