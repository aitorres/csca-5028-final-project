"""
Main entry point for the web application.
"""

import os
import logging
from typing import Final

import psycopg2
from flask import Flask, render_template

logger = logging.getLogger(__name__)

# PostgreSQL configuration, default dummy value used on local tests
# but real value is expected to be set in the environment
POSTGRESQL_URL: Final[str] = os.environ.get(
    "POSTGRESQL_URL",
    "postgresql://postgres:password@localhost:5432/mydatabase"
)

app: Flask = Flask(__name__)


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Get or create the database connection.

    This function ensures that the database connection is established
    only once per hour and reused for subsequent requests, and also that
    we can run unit tests without needing a real database connection.

    :return: A psycopg2 connection object to the PostgreSQL database.
    """

    return psycopg2.connect(POSTGRESQL_URL)


@app.route("/api/posts/count", methods=["GET"])
def get_post_count() -> tuple[dict, int]:
    """
    API route to retrieve the total number of posts, useful
    for the front-end to notify users about new available posts.
    """

    logger.info("Post count API route accessed")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts")
    count = cursor.fetchone()[0]
    cursor.close()

    return {"count": count}, 200


@app.route("/api/posts", methods=["GET"])
def get_posts() -> tuple[list[dict], int]:
    """
    API route to retrieve posts.
    """

    logger.info("Posts API route accessed")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, content, sentiment, inserted_at, created_at, source
        FROM posts
        ORDER BY created_at DESC, id DESC
        """
    )
    posts = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": post[0],
            "text": post[1],
            "sentiment": post[2],
            "inserted_at": post[3],
            "created_at": post[4],
            "source": post[5]
        } for post in posts
    ], 200


@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check() -> tuple[str, int]:
    """
    Health check route to verify the application is running.
    """

    logger.debug("Health check route accessed")
    return "ok", 200


@app.route("/", methods=["GET"])
def home() -> str:
    """
    Home route that returns a welcome message.
    """

    logger.info("Home route accessed")
    return render_template("home.html")


def main() -> None:
    """
    Main function to start the web application.
    """

    logger.info("Starting the web application...")
    app.run()


if __name__ == "__main__":
    main()
