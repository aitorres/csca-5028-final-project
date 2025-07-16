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


async def process_websocket_message(message: str) -> None:
    """
    Processes a message received from the WebSocket connection,
    which represents a Bluesky Jetstream event.
    """

    parse_and_filter_record(message)


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
