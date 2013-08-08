"""
Models for representation of search results
"""

import json
import string
import re
from collections import Counter

import search.sorting
from xmodule.modulestore import Location

import nltk
import nltk.corpus as word_filter


class SearchResults:
    """
    This is a collection of all search results to a query.

    In addition to extending all of the standard collection methods (__len__, __getitem__, etc...)
    this lets you use custom sorts and filters on the included search results.
    """

    def __init__(self, response, **kwargs):
        """kwargs should be the GET parameters from the original search request
        filters needs to be a dictionary that maps fields to allowed values"""
        raw_results = json.loads(response.content).get("hits", {"hits": ""})["hits"]
        scores = [entry["_score"] for entry in raw_results]
        self.sort = kwargs.get("sort", None)
        raw_data = [entry["_source"] for entry in raw_results]
        self.query = " ".join(kwargs.get("s", "*.*"))
        results = zip(raw_data, scores)
        self.entries = [SearchResult(entry, score, self.query) for entry, score in results]
        self.filters = kwargs.get("filters", {"": ""})

    def sort_results(self):
        """
        Applies an in-place sort of the entries associated with the search results

        Sort type is specified in object initialization
        """

        self.entries = search.sorting.sort(self.entries, self.sort)

    def get_counter(self, field):
        """
        Returns a Counter (histogram) for the field indicated
        """

        master_list = [entry.data[field].lower() for entry in self.entries]
        return Counter(master_list)

    def filter(self, field, value):
        """
        Returns a set of all entries where the value of the specified field matches the specified value
        """

        if value is None:
            value = ""
        punc = re.compile('[%s]' % re.escape(string.punctuation))
        strip_punc = lambda s: punc.sub("", s).lower()
        to_filter = lambda value, entry, field: strip_punc(value) in strip_punc(entry.data.get(field, ""))
        return set(entry for entry in self.entries if to_filter(value, entry, field))

    def filter_and_sort(self):
        """
        Applies all relevant filters and sorts to the internal entries container
        """

        full_results = set()
        for field, value in self.filters.items():
            full_results |= self.filter(field, value)
        self.entries = list(full_results)
        self.sort_results()

    def __len__(self):
        """
        Implementation of len method standard to Containers

        It's useful to treat SearchResults as a Container in views from a usability perspective,
        so this class implements the standard gambit of Container methods
        """

        return len(self.entries)

    def __delitem__(self, i):
        """
        Deletes SearchResult at indicated index
        """

        del self.entries[i]

    def __getitem__(self, i):
        """
        Returns SearchResult at indicated index
        """

        return self.entries[i]

    def __setitem__(self, i, value):
        """
        Sets the SearchResult at indicated index to the specified value

        Value can be passed in either as a SearchResult, a list/tuple of values
        order as entry, score, query, or a dictionary with values for the keys
        entry, score, and query.
        """

        if isinstance(value, SearchResult):
            self.entries[i] = value
        elif isinstance(value, list):
            new_result = SearchResult(*value)
            self.entries[i] = new_result
        elif isinstance(value, dict):
            new_result = SearchResult(**value)
            self.entries[i] = new_result
        else:
            raise ValueError


class SearchResult:
    """
    A single element from the Search Results collection
    """

    def __init__(self, entry, score, query):
        self.data = entry
        self.url = _jump_to_url(entry)
        self.score = score
        self.thumbnail = "data:image/jpg;base64," + entry["thumbnail"]
        self.snippets = snippet_generator(self.data["searchable_text"], query)

def snippet_generator(transcript, query, soft_max=50, word_margin=25, bold=True):
    """
    This returns a relevant snippet from a given search item with direct matches highlighted.

    The intention is to break the text up into sentences, identify the first occurence of a search
    term within the text, and start the snippet at the beginning of that sentence.

    e.g: Searching for "history", the start of the snippet for a search result that contains "history"
    would be the first word of the first sentence containing the word "history"

    If no direct match is found the start of the document is used as the snippet.

    The bold flag determines whether or not the matching terms should be wrapped in a tag.

    The soft_max is the number of words at which we stop actively indexing (normally the snippeting works
    on full sentences, so when the soft_max is reached the snippet will stop at the end of that sentence.)

    The word margin is the maximum number of words past the soft max we allow the snippet to go. This might
    result in truncated snippets.
    """

    punkt = nltk.data.load('tokenizers/punkt/english.pickle')
    stop_words = word_filter.stopwords.words("english")
    sentences = punkt.tokenize(transcript)
    substrings = _query_reduction(query, stop_words)
    query_container = lambda sentence: any(substring in sentence.lower() for substring in substrings)
    tripped = False
    response = ""
    for sentence in sentences:
        if not tripped:
            if query_container(sentence):
                tripped = True
                response += sentence
        else:
            if (len(response.split()) + len(sentence.split()) < soft_max):
                response += " " + sentence
            else:
                response += " " + " ".join(sentence.split()[:word_margin])
                break
    # If this is a phonetic match, there might not be a direct text match
    if tripped is False:
        for sentence in sentences:
            if (len(response.split()) + len(sentence.split())) < soft_max:
                response += " " + sentence
            else:
                response += " " + " ".join(sentence.split()[:word_margin])
                break
    if bold:
        response = _match_highlighter(query, response)
    return response


def _match(words):
    """
    Determines whether two words are close enough to each other to be called a "match"

    The check is whether one of the words contains each other and if their lengths are within
    a relatively small tolerance of each other.
    """

    contained = lambda words: (words[0] in words[1]) or (words[1] in words[0])
    near_size = lambda words: abs(len(words[0]) - len(words[1])) < (len(words[0]) + len(words[1])) / 6
    return contained(words) and near_size(words)


def _query_reduction(query, stopwords):
    return [word.lower() for word in query.split() if word not in stopwords]


def _match_highlighter(query, response, tag="b", css_class="highlight", highlight_stopwords=True):
    wrapping = ("<" + tag + " class=" + css_class + ">", "</" + tag + ">")
    punctuation_map = dict((ord(char), None) for char in string.punctuation)
    depunctuation = lambda word: word.translate(punctuation_map)
    wrap = lambda text: wrapping[0] + text + wrapping[1]
    stop_words = word_filter.stopwords.words("english") * (not highlight_stopwords)
    query_set = set(_query_reduction(query, stop_words))
    bold_response = ""
    for word in response.split():
        if any(_match((query_word, depunctuation(word.lower()))) for query_word in query_set):
            bold_response += wrap(word) + " "
        else:
            bold_response += word + " "
    return bold_response


def _jump_to_url(entry):
    fields = ["tag", "org", "course", "category", "name"]
    location = Location(*[json.loads(entry["id"])[field] for field in fields])
    url = '{0}/{1}/jump_to/{2}'.format('/courses', entry["course_id"], location)
    return url
