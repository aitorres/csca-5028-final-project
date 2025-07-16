"""
Main entry point for the analyzer application.
"""

import logging

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure NLTK resources are downloaded
for resource in ["stopwords", "punkt_tab", "wordnet", "tokenizers"]:
    nltk.download(resource)

logger = logging.getLogger(__name__)


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


def main():
    """
    Main function to start the analyzer application.
    """

    logger.info("Starting the analyzer application...")


if __name__ == "__main__":
    main()
