"""Provides a function to convert html to plaintext."""
from bs4 import BeautifulSoup


def html_to_text(html_message, *args, **kwargs):
    """
    Converts an html message to plaintext.
    """
    soup = BeautifulSoup(html_message, *args, **kwargs)
    text = soup.get_text()
    return text
