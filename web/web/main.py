"""
Main entry point for the web application.
"""

import os
import logging
from typing import Final

import psycopg2
from flask import Flask, render_template, request

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
    cursor_data = cursor.fetchone()
    count = cursor_data[0] if cursor_data else 0
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


@app.route("/api/posts/statistics/sources", methods=["GET"])
def get_post_source_statistics() -> tuple[dict, int]:
    """
    API route to retrieve statistics about post sources,
    used by the front-end to display a pie chart.
    """

    logger.info("Post source statistics API route accessed")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT source, COUNT(*) as count
        FROM posts
        GROUP BY source
        """
    )
    results = cursor.fetchall()
    cursor.close()

    data = {
        "labels": [row[0] for row in results],
        "data": [row[1] for row in results]
    }
    return data, 200


@app.route("/api/posts/statistics/sentiment", methods=["GET"])
def get_post_sentiment_statistics() -> tuple[dict, int]:
    """
    API route to retrieve statistics about post sentiment,
    used by the front-end to display a pie chart.

    Query parameters:
        hours: Optional integer representing hours to look back.
                  If not provided, defaults to 24 hours.
    """

    logger.info("Post sentiment statistics API route accessed")

    # Base query
    query = """
        SELECT sentiment, COUNT(*) as count
        FROM posts
    """

    # Retrieving and validating the 'hours' query parameter if it exists
    hours_param = request.args.get('hours', None)
    if hours_param is not None:
        try:
            hours = int(hours_param)

            if hours <= 0:
                return {"error": "If specified, hours must be a positive integer"}, 400

            # The hours parameter is valid, filter by hours on the query
            query += f"WHERE created_at >= NOW() - INTERVAL '{hours} hours' "
        except ValueError:
            return {"error": "If specified, hours must be a valid integer"}, 400

    # Finalize the query by grouping by sentiment
    query += "GROUP BY sentiment"

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    data = {
        "labels": [row[0] for row in results],
        "data": [row[1] for row in results]
    }
    return data, 200


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
