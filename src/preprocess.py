"""
preprocess.py

This module cleans the extracted resume text.
"""

import re


def clean_text(text):
    """
    Clean resume text by:
    - Converting to lowercase
    - Removing URLs
    - Removing punctuation
    - Removing special characters
    - Removing extra spaces

    Args:
        text (str): Raw extracted text.

    Returns:
        str: Cleaned text.
    """

    # Convert text to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove punctuation and special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()
