"""
Module for unit tests that cover the analyzer application's main module.
"""

import pytest

from analyzer.main import analyze_sentiment, preprocess_text


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
