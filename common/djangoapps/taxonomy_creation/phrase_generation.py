"""
Given a piece of content this aims to generate a relevant set of search terms to generate mediawiki-based tags
"""

from pymarkov import markov
from nltk.tokenize import word_tokenize, sent_tokenize


def _get_master_dict(content):
    """
    Given a piece of written content, creates a markov dictionary sentence by sentence
    """

    return markov.train(sent_tokenize(content), 1, split_callback=word_tokenize)


def _get_frequency_distribution(markov_dict):
    """
    Takes the master markov dictionary and returns a counter distribution of the entire set
    """

    values = lambda counter: (value for key, value in counter.iteritems())
    distribution = [values(entry) for key,entry in markov_dict[1].iteritems()]