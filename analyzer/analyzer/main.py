"""
Main entry point for the analyzer application.
"""

import asyncio
import json
import logging
import os
from typing import Final

import nltk
import pika
import psycopg2
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from pika.adapters.blocking_connection import BlockingChannel

# Ensure NLTK resources are downloaded
for resource in ["stopwords", "punkt_tab", "wordnet", "vader_lexicon"]:
    nltk.download(resource)

logger = logging.getLogger(__name__)

# RabbitMQ configuration, default dummy values used on local tests
# but all values are expected to be set in the environment
# when deployed.
RABBITMQ_HOST: Final[str] = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT: Final[int] = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER: Final[str] = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD: Final[str] = os.environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE_NAME: Final[str] = os.environ.get("RABBITMQ_QUEUE_NAME", "queue")

# PostgreSQL configuration, default dummy value used on local tests
# but real value is expected to be set in the environment
POSTGRESQL_URL: Final[str] = os.environ.get(
    "POSTGRESQL_URL",
    "postgresql://postgres:password@localhost:5432/mydatabase"
)

# Delay in seconds before polling the RabbitMQ queue
POLLING_DELAY: Final[int] = 3

# Sentiment analyzer and constants
sentiment_analyzer = SentimentIntensityAnalyzer()
SENTIMENT_THRESHOLD: Final[float] = 0.40
SENTIMENT_POSITIVE: Final[str] = "positive"
SENTIMENT_NEUTRAL: Final[str] = "neutral"
SENTIMENT_NEGATIVE: Final[str] = "negative"


def setup_database_connection() -> psycopg2.extensions.connection:
    """
    Sets up the database connection for the analyzer application.

    :return: An SQLAlchemy Engine instance connected to the database.
    """

    return psycopg2.connect(POSTGRESQL_URL)


def setup_queue() -> BlockingChannel:
    """
    Sets up the RabbitMQ queue for the analyzer application.

    :return: A BlockingChannel instance connected to the RabbitMQ server.
    """

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )

    connection = pika.BlockingConnection(parameters)
    channel: BlockingChannel = connection.channel()

    channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)

    return channel


def preprocess_text(text: str) -> str:
    """
    Given an input string, preprocesses it by performing
    common NLP cleanup tasks such as tokenization and removal
    of stop words.

    :param text: The input text to preprocess.
    :return: The preprocessed text.
    """

    # Clean up any extra whitespace and standardize case
    text = text.strip().lower()

    # Tokenize the text
    tokens = word_tokenize(text)

    # Remove stop words
    tokens = [
        token
        for token in tokens
        if token not in stopwords.words("english") and token.isalpha()
    ]

    # Lemmatize tokens
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    return " ".join(tokens)


def analyze_sentiment(text: str) -> str:
    """
    Given an input string which is assumed preprocessed,
    calculates the sentiment of the text by using NLTK
    VADER sentiment analysis.

    We get a compound score and classify it as positive,
    neutral, or negative based on a threshold.

    :param text: The preprocessed text to analyze.
    :return: The sentiment classification as a string.
    """

    score = sentiment_analyzer.polarity_scores(text)["compound"]

    if score >= SENTIMENT_THRESHOLD:
        return SENTIMENT_POSITIVE

    if score <= -SENTIMENT_THRESHOLD:
        return SENTIMENT_NEGATIVE

    return SENTIMENT_NEUTRAL


def process_queue_message(db: psycopg2.extensions.connection, message: str) -> None:
    """
    Given a message from the RabbitMQ queue,
    processes it by parsing the record, then performs
    NLP preprocessing and sentiment analysis and stores the result.

    :param db_engine: The SQLAlchemy engine for database operations.
    :param message: The message received from the RabbitMQ queue.
    """

    message = message.strip()
    if not message:
        return

    logger.info("Processing message from RabbitMQ queue: %s", message)

    try:
        record = json.loads(message)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON message: %s", e)
        return

    if not isinstance(record, dict):
        logger.error("Record is not a dictionary: %s", record)
        return

    if any(key not in record for key in ["text", "createdAt", "source"]):
        logger.error("Record is missing required fields: %s", record)
        return

    text = record["text"]
    preprocessed_text = preprocess_text(text)
    logger.info("Preprocessed text: %s", preprocessed_text)

    sentiment = analyze_sentiment(preprocessed_text)
    logger.info("Sentiment analysis result: %s", sentiment)

    cursor = db.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO posts (content, sentiment, created_at, source)
            VALUES (%s, %s, %s, %s)
            """,
            (
                text,
                sentiment,
                record["createdAt"],
                record["source"]
            )
        )
        db.commit()
    except psycopg2.Error as e:
        logger.error("Database error occurred: %s", e)
        db.rollback()
        return
    else:
        logger.info("Sentiment analysis result stored in the database.")
    finally:
        cursor.close()


async def main():
    """
    Main function to start the analyzer application.
    """

    logger.info("Starting the analyzer application...")

    logger.info("Setting up database engine...")
    db = setup_database_connection()
    logger.info("Database engine established successfully.")

    logger.info("Setting up RabbitMQ queue...")
    channel = setup_queue()
    logger.info("RabbitMQ queue '%s' is set up successfully.", RABBITMQ_QUEUE_NAME)

    logger.info("Setting up RabbitMQ consumer...")
    channel.basic_consume(
        queue=RABBITMQ_QUEUE_NAME,
        on_message_callback=lambda _ch, _m, _p, body: process_queue_message(
            db, body.decode('utf-8')
        ),
        auto_ack=True,
    )

    logger.info("RabbitMQ consumer is set up successfully. Listening now!")
    channel.start_consuming()


if __name__ == "__main__":
    asyncio.run(main())
