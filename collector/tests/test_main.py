"""
Unit tests for the collector application's main module.
"""

from typing import Any, Optional

import pytest

from collector.main import (
    filter_record_by_content,
    parse_and_filter_record,
    process_websocket_event,
    transform_record_to_message,
    RABBITMQ_EXCHANGE_NAME,
    RABBITMQ_QUEUE_NAME,
)


@pytest.mark.parametrize(
    "message, expected",
    [
        ("", None),
        ("   ", None),
        ("invalid json", None),
        ("[]", None),
        ("{}", None),
    ]
)
def test_parse_and_filter_record(
    message: str, expected: Optional[dict[str, Any]]
) -> None:
    """
    Unit test for the parse_and_filter_record function with a combination
    of valid and invalid inputs, and their expected outputs.
    """

    assert parse_and_filter_record(message) == expected


@pytest.mark.parametrize(
    "record, expected",
    [
        (
            {"text": "This is a post about Vancouver"},
            {"text": "This is a post about Vancouver"}
        ),
        ({"text": "This is a post about Toronto"}, None),
        (
            {"text": "Vancouver is great!"},
            {"text": "Vancouver is great!"}
        ),
        ({"text": "I love Van"}, None),
        (
            {"text": "YVR is the best airport"},
            {"text": "YVR is the best airport"}
        ),
        ({"text": "Vancity vibes"}, {"text": "Vancity vibes"}),
        (
            {"text": "Nothing to do with Vancouver"},
            {"text": "Nothing to do with Vancouver"}
        ),
        (
            {"text": "Este es un post en otro idioma", "langs": ["es"]},
            None
        ),
        (
            {"text": "Este es un post en otro idioma sobre Vancouver", "langs": ["es"]},
            None
        ),
    ]
)
def test_filter_record_by_message(
    record: dict[str, Any], expected: Optional[dict[str, Any]]
) -> None:
    """
    Unit test for the filter_record_by_content function with various
    records and their expected outputs.
    """

    assert filter_record_by_content(record) == expected


@pytest.mark.parametrize(
    "input_record, expected_message",
    [
        (
            {"text": "This is a Vancouver post", "createdAt": "2023-10-01T12:00:00Z"},
            '{"source": "bluesky", "type": "post", "text": "This is a Vancouver post", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
        (
            {"text": "Vancouver is great!", "createdAt": "2023-10-01T12:00:00Z"},
            '{"source": "bluesky", "type": "post", "text": "Vancouver is great!", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
        (
            {"text": "YVR is the best airport", "createdAt": "2023-10-01T12:00:00Z"},
            '{"source": "bluesky", "type": "post", "text": "YVR is the best airport", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
    ]
)
def test_transform_record_to_message(
    input_record: dict[str, Any], expected_message: str
) -> None:
    """
    Unit test for the transform_record_to_message function with various
    records and their expected JSON string outputs.

    This validates that we correctly generate a JSON string
    that complies with the expected format for RabbitMQ messages, as well
    as our application's contract.
    """

    assert transform_record_to_message(input_record) == expected_message


@pytest.mark.parametrize(
    "input_message, message_expected, expected_body",
    [
        (
            '',
            False,
            None
        ),
        (
            '{"commit": {"record": {"$type": "app.bsky.feed.post", '
            '"text": "This is a Vancouver post", "createdAt": "2023-10-01T12:00:00Z"}}}',
            True,
            '{"source": "bluesky", "type": "post", "text": "This is a Vancouver post", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
        (
            '{"commit": {"record": {"$type": "app.bsky.feed.post", '
            '"text": "This is Toronto post", "createdAt": "2023-10-01T12:00:00Z"}}}',
            False,
            None
        ),
        (
            '{"commit": {"record": {"$type": "app.bsky.feed.post", '
            '"text": "Vancouver is great!", "createdAt": "2023-10-01T12:00:00Z"}}}',
            True,
            '{"source": "bluesky", "type": "post", "text": "Vancouver is great!", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
        (
            '{"commit": {"record": {"$type": "app.bsky.feed.post", '
            '"text": "I love Van", "createdAt": "2023-10-01T12:00:00Z"}}}',
            False,
            None
        ),
        (
            '{"commit": {"record": {"$type": "app.bsky.feed.post", '
            '"text": "YVR is the best airport", "createdAt": "2023-10-01T12:00:00Z"}}}',
            True,
            '{"source": "bluesky", "type": "post", "text": "YVR is the best airport", '
            '"createdAt": "2023-10-01T12:00:00Z"}'
        ),
    ]
)
def test_process_websocket_message(
    mocker,
    input_message: str,
    message_expected: bool,
    expected_body: Optional[str]
) -> None:
    """
    Unit test for the function that processes each message received from
    the websocket connection.

    Mocks the RabbitMQ channel to ensure that the message is processed as expected
    through a spy.
    """

    # Setup a mock and spy for the RabbitMQ channel
    channel_mock = mocker.Mock()
    channel_spy = mocker.spy(channel_mock, "basic_publish")

    # Call the function with the mocked channel and input message
    process_websocket_event(input_message, channel_mock)

    if not message_expected:
        # If no message is expected in this test case,
        # assert that basic_publish was not called
        channel_spy.assert_not_called()
    else:
        # If a message is expected, assert that basic_publish was called
        channel_spy.assert_called_once()
        _, kwargs = channel_spy.call_args

        # Validate rabbitmq details
        assert kwargs["routing_key"] == RABBITMQ_QUEUE_NAME

        # Validate the body of the message
        assert expected_body is not None
        assert kwargs["body"] == expected_body
