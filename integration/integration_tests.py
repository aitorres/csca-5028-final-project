"""
This module contains a very basic integration test leveraging
the local `docker compose` setup, consider it as a smoketest
to ensure the application components can run and work together.
"""

import json
import uuid
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
        sys.exit(1)
except urllib.error.URLError as e:
    print(f"Failed to connect to the application: {e.reason}")
    sys.exit(1)

# Step 3. Submit a post to the application
print("Submitting a test post to the application...")
random_string = str(uuid.uuid4())
data = {
    "content": f"This is a test post for integration testing with a random string: {random_string}.",
}

try:
    req = urllib.request.Request(
        LOCALHOST_URL + "/api/posts",
        data=json.dumps(data).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    response = urllib.request.urlopen(req)
    if response.status == 201:
        print("Post submitted successfully.")
    else:
        print(f"Failed to submit post, status code: {response.status}")
        print("Response:", response.read().decode('utf-8'))
        sys.exit(1)
except urllib.error.HTTPError as e:
    print(f"Error submitting post: {e.reason}")
    print("Error response content:", e.read().decode('utf-8'))
    print("Retrieving web service logs for debugging...")
    os.system("docker compose logs web --tail=10")
    sys.exit(1)

# Wait for a while to ensure the post is processed
print("Waiting for the post to be processed...")
time.sleep(15)

# Step 4. Retrieve posts to verify the submission
print("Retrieving posts to verify submission...")
try:
    response = urllib.request.urlopen(LOCALHOST_URL + "/api/posts")
    if response.status == 200:
        posts = response.read().decode('utf-8')
        print("Posts retrieved successfully:")
        posts_data = json.loads(posts)

        found = False
        for post in posts_data:
            if found:
                break

            if random_string in post['text']:
                print("Test post found in the retrieved posts.")
                found = True

        if not found:
            print("Test post not found in the retrieved posts.")
            sys.exit(1)
        else:
            print("All checks passed, test post is present.")
    else:
        print(f"Failed to retrieve posts, status code: {response.status}")
        sys.exit(1)
except urllib.error.URLError as e:
    print(f"Error retrieving posts: {e.reason}")
    sys.exit(1)

# Cleanup: Shut down the application
print("Shutting down the application...")
os.system("docker compose down")

print("Integration test completed successfully!")
