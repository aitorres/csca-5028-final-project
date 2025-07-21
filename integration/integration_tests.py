"""
This module contains a very basic integration test leveraging
the local `docker compose` setup, consider it as a smoketest
to ensure the application components can run and work together.
"""

import time
import os
import sys
import urllib.request
from typing import Final

LOCALHOST_URL: Final[str] = "http://localhost:8080"


# Step 1. Boot up the application using docker compose
print("Starting the application using docker compose...")
os.system("docker compose up -d --build")

# Step 2. Wait for the application to be ready
time.sleep(30)

# Step 3. Check if the application is running
# by hitting the healthcheck
try:
    response = urllib.request.urlopen(LOCALHOST_URL + "/api/health")
    if response.status == 200:
        print("Application is running successfully.")
    else:
        print(f"Unexpected status code: {response.status}")
except urllib.error.URLError as e:
    print(f"Failed to connect to the application: {e.reason}")
    sys.exit(1)

# Cleanup: Shut down the application
print("Shutting down the application...")
os.system("docker compose down")

print("Integration test completed successfully!")
