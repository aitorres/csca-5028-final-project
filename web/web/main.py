"""
Main entry point for the web application.
"""

import logging

from flask import Flask


app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route("/", methods=["GET"])
def home():
    """
    Home route that returns a welcome message.
    """

    logger.info("Home route accessed")
    return "Welcome to the Web Application!"


def main():
    """
    Main function to start the web application.
    """

    logger.info("Starting the web application...")
    app.run()


if __name__ == "__main__":
    main()
