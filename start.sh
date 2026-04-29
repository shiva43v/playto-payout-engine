#!/bin/bash

# Change to the backend directory
cd backend || exit

# Start Celery worker in the background
celery -A config worker -l info &

# Start Celery beat in the background
celery -A config beat -l info &

# Start the web server in the foreground
gunicorn config.wsgi:application
