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
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from pika.adapters.blocking_connection import BlockingChannel

# Ensure NLTK resources are downloaded
for resource in ["stopwords", "punkt_tab", "wordnet"]:
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

# Delay in seconds before polling the RabbitMQ queue
POLLING_DELAY: Final[int] = 3


def setup_queue() -> BlockingChannel:
    """
    Sets up the RabbitMQ queue for the collector application.
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


def process_queue_message(message: str) -> None:
    """
    Given a message from the RabbitMQ queue,
    processes it by parsing the record, then performs
    NLP preprocessing and sentiment analysis and stores the result.

    :param message: The message received from the RabbitMQ queue.
    """

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

    text = record["text"]
    preprocessed_text = preprocess_text(text)
    logger.info("Preprocessed text: %s", preprocessed_text)


async def main():
    """
    Main function to start the analyzer application.
    """

    logger.info("Starting the analyzer application...")

    logger.info("Setting up RabbitMQ queue...")
    channel = setup_queue()
    logger.info("RabbitMQ queue '%s' is set up successfully.", RABBITMQ_QUEUE_NAME)

    # Set up a RabbitMQ consumer
    logger.info("Setting up RabbitMQ consumer...")
    channel.basic_consume(
        queue=RABBITMQ_QUEUE_NAME,
        on_message_callback=lambda _ch, _m, _p, body: process_queue_message(
            body.decode('utf-8')
        ),
        auto_ack=True,
    )

    logger.info("RabbitMQ consumer is set up successfully. Listening now!")
    channel.start_consuming()


if __name__ == "__main__":
    asyncio.run(main())
