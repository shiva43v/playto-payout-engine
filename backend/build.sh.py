#!/usr/bin/env python
# Build script for Render

import os
import subprocess
import sys

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding or 'utf-8'))
    process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        print(f"Command failed with return code {return_code}")
        sys.exit(return_code)

# Change directory to backend
os.chdir("backend")

# Install dependencies
run_command("pip install -r requirements.txt")

# Run migrations
run_command("python manage.py migrate")

# Collect static files
run_command("python manage.py collectstatic --no-input")

# Seed data if requested (using an env var to trigger)
if os.environ.get("SEED_DB", "false").lower() == "true":
    run_command("python seed.py")
