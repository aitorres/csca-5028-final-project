"""
Main entry point for the web application.
"""

import logging

from flask import Flask, render_template

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
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
