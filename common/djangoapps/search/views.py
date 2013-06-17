from django.http import HttpResponse, Http404
from django.core.context_processors import csrf
from mitxmako.shortcuts import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import requests
import json
import nltk.data
import nltk.corpus as word_filter
import enchant
import string


def search(request):
    context = {}
    results_string = ""
    if request.GET:
        results_string = find(request)
        context.update({"old_query": request.GET['s']})
    search_bar = render_to_string("search.html", context)
    return HttpResponse(search_bar + results_string)


def find(request, database="http://127.0.0.1:9200",
         value_="transcript", field="searchable_text", max_result=100):
    query = request.GET.get("s", "")
    page = request.GET.get("page", 1)
    results_per_page = request.GET.get("results", 15)
    ordering = request.GET.get("ordering", False)
    index = request.GET.get("content", "transcript")+"-index"
    full_url = "/".join([database, index, value_, "_search?q="+field+":"])
    context = {}

    try:
        results = json.loads(requests.get(full_url+query+"&size="+str(max_result))._content)["hits"]["hits"]
        uuids = [entry["_source"]["uuid"] for entry in results]
        transcripts = [entry["_source"]["searchable_text"] for entry in results]
        snippets = [snippet_generator(transcript, query) for transcript in transcripts]
        data = zip(uuids, snippets)
        data = proper_page(page, data, results_per_page)
    except KeyError:
        data = ("No results found", "Please try again")
    context.update({"data": data})

    correction = spell_check(query)
    results_pages = Paginator(data, results_per_page)
    context.update({"spelling_correction": correction})
    return render_to_string("search_templates/results.html", context)


def query_reduction(query, stopwords):
    return [word.lower() for word in query.split() if word not in stopwords]


def proper_page(page, data, results_per_page=15):
    pages = Paginator(data, results_per_page)
    correct_page = ""
    try:
        correct_page = pages.page(page)
    except PageNotAnInteger:
        correct_page = pages.page(1)
    except EmptyPage:
        correct_page = pages.page(pages.num_pages)
    return correct_page


def match(words):
    contained = lambda words: (words[0] in words[1]) or (words[1] in words[0])
    near_size = lambda words: abs(len(words[0]) - len(words[1])) < (len(words[0])+len(words[1]))/6
    return contained(words) and near_size(words)


def match_highlighter(query, response, tag="b", css_class="highlight", highlight_stopwords=True):
    wrapping = ("<"+tag+" class="+css_class+">", "</"+tag+">")
    punctuation_map = dict((ord(char), None) for char in string.punctuation)
    depunctuation = lambda word: word.translate(punctuation_map)
    wrap = lambda text: wrapping[0] + text + wrapping[1]
    stop_words = word_filter.stopwords.words("english") * (not highlight_stopwords)
    query_set = set(query_reduction(query, stop_words))
    bold_response = ""
    for word in response.split():
        if any(match((query_word, depunctuation(word.lower()))) for query_word in query_set):
            bold_response += wrap(word) + " "
        else:
            bold_response += word + " "
    return bold_response


def snippet_generator(transcript, query, soft_max=50, word_margin=30, bold=True):
    punkt = nltk.data.load('tokenizers/punkt/english.pickle')
    stop_words = word_filter.stopwords.words("english")
    sentences = punkt.tokenize(transcript)
    substrings = query_reduction(query, stop_words)
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
        response = match_highlighter(query, response)
    return response


def spell_check(query, pyenchant_dictionary_file="common/djangoapps/search/pyenchant_corpus.txt", stopwords=set()):
    """Returns corrected version with attached html if there are suggested corrections."""
    dictionary = enchant.request_pwl_dict(pyenchant_dictionary_file)
    words = query_reduction(query, stopwords)
    possible_corrections = [dictionary.suggest(word)[0] for word in words]
    if possible_corrections == words:
        return None
    else:
        return " ".join(possible_corrections)
