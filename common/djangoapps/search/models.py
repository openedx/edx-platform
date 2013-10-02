"""
Models for representation of search results
"""

import json
import string  # pylint: disable=W0402

from django.conf import settings
import nltk
import nltk.stem.snowball as snowball
from nltk.stem import RegexpStemmer
from guess_language import guessLanguageName
import logging

import search.sorting
from xmodule.modulestore import Location

log = logging.getLogger(__name__)

"""
The soft_max is the number of words at which we stop actively indexing (normally the snippeting works
on full sentences, so when the soft_max is reached the snippet will stop at the end of that sentence.)
"""

SOFT_MAX = 50

"""
The word margin is the maximum number of words past the soft max we allow the snippet to go. This might
result in truncated snippets.
"""

WORD_MARGIN = 25


class SearchResults(object):
    """
    This is a collection of all search results to a query.

    It will automatically sort itself according to a sort parameter passed in as a kwarg.
    The sort method should be added to search.sorting. The existing sort methods should be
    decent for outlining how a sort works.
    """

    def __init__(self, response, **kwargs):
        """
        kwargs should be the GET parameters from the original search request
        filters needs to be a dictionary that maps fields to allowed values
        """
        raw_results = json.loads(response.content).get("hits", {"hits": []})["hits"]
        self.query = kwargs.get("s", "")
        if not self.query:
            self.entries = []
        else:
            entries = [SearchResult(entry, self.query) for entry in raw_results]
            sort = kwargs.get("sort", "relevance")
            self.entries = search.sorting.sort(entries, sort)

    def get_category(self, category):
        """
        Returns a subset of all results that match the given category

        If you pass in an empty category the default is to return everything
        """

        if category == "all" or category is None:
            return self.entries
        else:
            return [entry for entry in self.entries if entry.category == category]

    def get_page(self, page_number, category, results_per_page):
        """
        Returns the specific results of a given page in the set of search results with the given category.

        Casts results to dictionary to ensure that Javascript will be able to intepret this without any failings.
        """

        results = self.get_category(category)
        sliced_results = results[((page_number - 1) * results_per_page): page_number * results_per_page]
        return [result.__dict__ for result in sliced_results]


class SearchResult(object):
    """
    A single element from the Search Results collection
    """

    def __init__(self, entry, query):
        self.data = entry["_source"]
        self.category = json.loads(self.data["id"])["category"]
        self.url = _return_jump_to_url(self.data)
        self.score = entry["_score"]
        if self.data["thumbnail"].startswith("/static/"):
            self.thumbnail = _get_content_url(self.data, self.data["thumbnail"])
        else:
            self.thumbnail = self.data["thumbnail"]
        language = guessLanguageName(self.data["searchable_text"]).lower()
        self.snippets = _snippet_generator(self.data["searchable_text"], query[0], language)


def _get_content_url(data, static_url):
    """
    Generates a real content url for problems specified with static urls

    Nobody seems to know how this works, but this hack works for everything I can find.
    """

    base_url = "/c4x/%s/%s/asset" % (json.loads(data["id"])["org"], json.loads(data["id"])["course"])
    addendum = static_url.replace("/static/", "")
    current = "/".join([base_url, addendum])
    substring = current[current.find("images/"):].replace("/", "_")
    substring = current[:current.find("/images")] + "/" + substring
    return substring


def _snippet_generator(transcript, query, language):
    """
    This returns a relevant snippet from a given search item with direct matches highlighted.

    The intention is to break the text up into sentences, identify the first occurence of a search
    term within the text, and start the snippet at the beginning of that sentence.

    e.g: Searching for "history", the start of the snippet for a search result that contains "history"
    would be the first word of the first sentence containing the word "history"

    If no direct match is found the start of the document is used as the snippet.

    The bold flag determines whether or not the matching terms should be wrapped in a tag.

    For sentence tokenization, we allow a setting, if it is set then we will just use that tokenizer.
    Otherwise we will try to guess the language of the transcript and use the appropriate punkt tokenizer.
    If that fails, or we don't have an appropriate tokenizer we will just assume that periods are appropriate
    sentence delimiters, and if they are things work without condition. Otherwise this tokenizer will just
    start from the beginning of the transcript.
    """

    if settings.SENTENCE_TOKENIZER and settings.SENTENCE_TOKENIZER.lower() != "detect":
        punkt = nltk.data.load(settings.SENTENCE_TOKENIZER)
        sentences = punkt.tokenize(transcript)  # pylint disable=E1103
    else:
        try:
            punkt = nltk.data.load('tokenizers/punkt/%s.pickle' % language)
            sentences = punkt.tokenize(transcript)  # pylint disable=E1103
        except LookupError:
            sentences = transcript.split(".")

    query_set = set([_clean(word, language) for word in query.split()])
    get_sentence_stem_set = lambda sentence: set([_clean(word, language) for word in sentence.split()])
    stem_match = lambda sentence: bool(query_set.intersection(get_sentence_stem_set(sentence)))
    snippet_start = next((i for i, sentence in enumerate(sentences) if stem_match(sentence)), 0)
    response = ""
    for sentence in sentences[snippet_start:]:
        if (len(response.split()) + len(sentence.split()) < SOFT_MAX):
            response += " " + sentence
        else:
            response += " " + " ".join(sentence.split()[:WORD_MARGIN])
            break
    response = _highlight_matches(query, response, language)
    return response


def _clean(term, language):
    """
    Returns a standardized or "cleaned" version of the term

    Specifically casts to lowercase, removes punctuation, and stems.

    stemming is either defined in settings, or discovered through the implied
    language of the transcript
    """

    if settings.STEMMER and settings.STEMMER.lower() != "detect":
        stemmer = getattr(snowball, "%sStemmer" % settings.STEMMER.title())()
    else:
        try:
            stemmer = getattr(snowball, "%sStemmer" % language.title())()
        except AttributeError:
            # Blank stemmer to keep things parallel and sensible.
            stemmer = RegexpStemmer("")
    if isinstance(term, unicode):
        punctuation_map = {ord(char): None for char in string.punctuation}
        rinsed_term = term.translate(punctuation_map)
    else:
        rinsed_term = term.translate(None, string.punctuation)
    return stemmer.stem(rinsed_term.lower())


def _highlight_matches(query, response, language):
    """
    Highlights all direct matches within given snippet
    """

    query_set = set([_clean(word, language) for word in query.split()])
    wrap = lambda word: '<b class="highlight">%s</b> ' % word
    return " ".join([wrap(word) if (_clean(word, language) in query_set) else (word) for word in response.split()])


def _return_jump_to_url(entry):
    """
    Generates the proper jump_to url for a given entry
    """

    fields = ["tag", "org", "course", "category", "name"]
    location = Location(*[json.loads(entry["id"])[field] for field in fields])
    url = '/courses/{0}/jump_to/{1}'.format(entry["course_id"], location)
    return url
