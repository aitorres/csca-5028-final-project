"""
Main entry point for the collector application.
"""

import asyncio
import json
import logging
from typing import Any, Final, Optional

from websockets.asyncio.client import connect

logger = logging.getLogger(__name__)

# The Jetstream is a websocket endpoint that represents Bluesky's real-time data stream,
# we can listen to it to receive updates about posts, likes, follows, etc.
BLUESKY_JETSTREAM_WEBSOCKET_URL: Final[str] = (
    "wss://jetstream2.us-east.bsky.network/subscribe"
    "?wantedCollections=app.bsky.feed.post"
)

# Terms to use for filtering posts related to Vancouver
VANCOUVER_FILTER_TERMS: Final[list[str]] = [
    "vancouver",
    "yvr",
    "vancity",
    "vancouverbc",
]


def parse_and_filter_record(message: str) -> Optional[dict[str, Any]]:
    """
    Given a message from the WebSocket connection,
    parses it as a JSON object and filters it to exclude everything
    that is not a Bluesky post (which is what we want to collect).

    :param message: The message received from the WebSocket connection.
    :return: A dictionary containing the filtered message record, or None.
    """

    try:
        data = json.loads(message)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON message: %s", e)
        return None

    if "commit" not in data:
        return None

    commit = data["commit"]
    if "record" not in commit:
        return None

    record = commit["record"]
    if "$type" not in record or record["$type"] != "app.bsky.feed.post":
        return None

    # We have a valid Bluesky post, return the record!
    assert isinstance(record, dict), "Record should be a dictionary"
    return record


def filter_record_by_message(record: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Given a Bluesky post record from the WebSocket connection,
    filters it to include only posts in English that are related
    to the city of Vancouver.

    :param record: The Bluesky post record to filter.
    :return: The record if it matches the criteria, or None.
    """

    if "langs" in record and record["langs"] and "en" not in record["langs"][0]:
        return None

    if "text" not in record or not isinstance(record["text"], str):
        return None

    text = record["text"].lower()

    if any(term in text for term in VANCOUVER_FILTER_TERMS):
        # The post is related to Vancouver, return it
        return record

    return None


async def process_websocket_message(message: str) -> None:
    """
    Processes a message received from the WebSocket connection,
    which represents a Bluesky Jetstream event.
    """

    record = parse_and_filter_record(message)

    if record is not None:
        filtered_record = filter_record_by_message(record)

        if filtered_record is not None:
            logger.info("Record related to Vancouver found: %s", filtered_record)


async def main():
    """
    Main function to start the collector application.
    """

    logger.info("Starting the collector application...")

    logger.info("Connecting to WebSocket at %s...", BLUESKY_JETSTREAM_WEBSOCKET_URL)
    async with connect(BLUESKY_JETSTREAM_WEBSOCKET_URL) as websocket:
        logger.info("Connected to Bluesky Jetstream WebSocket!")

        logger.info("Listening for messages from the WebSocket...")
        while True:
            message = await websocket.recv()
            await process_websocket_message(message)


if __name__ == "__main__":
    asyncio.run(main())
