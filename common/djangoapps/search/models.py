import json
import nltk
import nltk.corpus as word_filter
import string
import sorting
import re
from collections import Counter


class SearchResults:

    def __init__(self, request, response):
        self.results = json.loads(response._content).get("hits", {"hits": ""})["hits"]
        self.scores = [entry["_score"] for entry in self.results]
        self.request = request
        raw_data = [entry["_source"] for entry in self.results]
        self.query = request.GET.get("s", "*.*")
        results = zip(raw_data, self.scores)
        self.entries = [SearchResult(entry, score, self.query, request) for entry, score in results]
        self.has_results = len(self.entries) > 0

    def sort_results(self):
        self.entries = sorting.sort(self.entries, self.request.GET.get("sort", None))

    def get_counter(self, field):
        master_list = [entry.data[field].lower() for entry in self.entries]
        return Counter(master_list)

    def filter(self, field, value):
        if value is None:
            value = ""
        punc = re.compile('[%s]' % re.escape(string.punctuation))
        strip_punc = lambda s: punc.sub("", s)
        self.entries = [entry for entry in self.entries if strip_punc(value.lower()) in strip_punc(entry.data.get(field, "").lower())]


class SearchResult:

    def __init__(self, entry, score, query, request):
        self.data = entry
        self.data.update({"score": score})
        self.data.update({"thumbnail": "data:image/jpg;base64," + entry["thumbnail"]})
        self.data.update({"snippets": snippet_generator(self.data["searchable_text"], query)})
        self.data.update({"url": _update_url(request, self.data)})


def snippet_generator(transcript, query, soft_max=50, word_margin=25, bold=True):
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
            if (len(response.split())+len(sentence.split())) < soft_max:
                response += " " + sentence
            else:
                response += " " + " ".join(sentence.split()[:word_margin])
                break
    if bold:
        response = _match_highlighter(query, response)
    return response


def _match(words):
    contained = lambda words: (words[0] in words[1]) or (words[1] in words[0])
    near_size = lambda words: abs(len(words[0]) - len(words[1])) < (len(words[0])+len(words[1]))/6
    return contained(words) and near_size(words)


def _query_reduction(query, stopwords):
    return [word.lower() for word in query.split() if word not in stopwords]


def _match_highlighter(query, response, tag="b", css_class="highlight", highlight_stopwords=True):
    wrapping = ("<"+tag+" class="+css_class+">", "</"+tag+">")
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


def _update_url(request, datum):
    url = request.environ.get('HTTP_REFERER', "")
    host = request.environ.get("HTTP_HOST", "edx.org")
    trigger = "courseware"
    if trigger in url:
        base = url[:url.find(trigger)+len(trigger)+1]
        return base+datum["url"]
    else:
        return "http://" + host + "/courses/" + datum["course_section"]+"/courseware/" + datum["url"]
