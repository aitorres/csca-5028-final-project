"""
Module for unit tests that cover the analyzer application's main module.
"""

import json

import pytest

from analyzer.main import (
    analyze_sentiment,
    check_for_bad_words,
    preprocess_text,
    process_queue_message,
)


@pytest.mark.parametrize(
    "input_text, is_bad_word_expected",
    [
        ("This is a test.", False),
        ("This example has PUNCTUATION!", False),
        ("Another example, with some stop words.", False),
        ("  Leading and trailing spaces.  ", False),
        ("123 numbers should be ignored.", False),
        ("This phrase has a bad word: porn.", True),
        ("This phrase has a bad word: p0rn and damn.", True),
    ]
)
def test_check_for_bad_words(input_text: str, is_bad_word_expected: bool) -> None:
    """
    Unit tests to ensure bad word filtering is working as expected.
    """

    assert check_for_bad_words(input_text) == is_bad_word_expected


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("This is a test.", "test"),
        ("This example has PUNCTUATION!", "example punctuation"),
        ("Another example, with some stop words.", "another example stop word"),
        ("  Leading and trailing spaces.  ", "leading trailing space"),
        ("123 numbers should be ignored.", "number ignored"),
    ]
)
def test_preprocess_text(input_text: str, expected_output: str) -> None:
    """
    Unit tests to ensure text preprocessing is working as expected.

    :param input_text: The input text to preprocess.
    :param expected_output: The expected output after preprocessing.
    """

    assert preprocess_text(input_text) == expected_output


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("I love this product!", "positive"),
        ("This is okay, not great.", "neutral"),
        ("I hate waiting in line.", "negative"),
        ("", "neutral"),
        ("fish is delicious", "positive"),
        ("fish is awful and i hate it", "negative"),
        ("fish exists", "neutral"),
    ]
)
def test_analyze_sentiment(input_text: str, expected_output: str) -> None:
    """
    Unit tests to ensure sentiment analysis is working as expected.

    :param input_text: The preprocessed text to analyze.
    :param expected_output: The expected sentiment classification.
    """

    assert analyze_sentiment(input_text) == expected_output


@pytest.mark.parametrize(
    "message, is_valid_message",
    [
        ("", False),
        ("   ", False),
        ("invalid json", False),
        ("[]", False),
        ("{}", False),
        (
            '{"text": "This is a test post", "createdAt": "2023-10-01T12:00:00Z", '
            '"source": "bluesky"}',
            True
        ),
        (
            '{"text": "Another post", "createdAt": "2023-10-01T12:00:00Z", '
            '"source": "bluesky"}',
            True
        ),
        (
            '{"text": "Yet another post", "createdAt": "2023-10-01T12:00:00Z", '
            '"source": "bluesky"}',
            True
        ),
    ]
)
def test_process_queue_message(mocker, message: str, is_valid_message: bool) -> None:
    """
    Unit test for the function handler that processes each incoming
    message from the RabbitMQ queue, performing all validations and
    transformations as defined in the analyzer's main module before
    inserting into the database.

    The database connection is mocked and spied to ensure that the
    message is processed as expected, including the correct SQL
    execution with the expected parameters.

    :param mocker: The pytest-mock fixture to mock dependencies.
    """

    # Mock the database connection and cursor
    mock_db = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_db.cursor.return_value = mock_cursor

    # Call the function under test
    process_queue_message(mock_db, message)

    # If the message is invalid, ensure no SQL execution occurs
    if not is_valid_message:
        mock_cursor.execute.assert_not_called()
        return

    # If the message is valid, ensure SQL execution occurs
    mock_cursor.execute.assert_called_once()
    args, _ = mock_cursor.execute.call_args
    assert "INSERT INTO posts (content, sentiment, created_at, source)" in args[0]
    assert "VALUES" in args[0]

    parsed_message = json.loads(message)
    assert args[1][0] == parsed_message["text"]
    assert args[1][2] == parsed_message["createdAt"]
    assert args[1][3] == parsed_message["source"]
