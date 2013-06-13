from django.http import HttpResponse, Http404
from django.template import Context, RequestContext
from django.core.context_processors import csrf
from django.template.loader import render_to_string

import requests
import json
import nltk.data
import nltk.corpus as word_filter
import enchant
import os


def search(request):
    context = {}
    context.update((csrf(request)))
    results_string = ""
    if request.POST:
        results_string = find(request)
    search_bar = render_to_string("search.html", Context(context))
    return HttpResponse(search_bar + results_string)


def find(request, database="http://127.0.0.1:9200", index="transcript-index",
         value_="transcript", field="searchable_text"):
    query = request.POST['s']
    full_url = "/".join([database, index, value_, "_search?q="+field+":"])
    results = json.loads(requests.get(full_url+query)._content)["hits"]["hits"]
    uuids = [entry["_source"]["uuid"] for entry in results]
    transcripts = [entry["_source"]["searchable_text"] for entry in results]
    snippets = [snippet_generator(transcript, query) for transcript in transcripts]
    correction = spell_check(query)
    data = zip(uuids, snippets)
    context = {"data": data, "search_correction": correction}
    return render_to_string("search_templates/results.html", context, context_instance=RequestContext(request))


def query_reduction(query, stopwords):
    return [word.lower() for word in query.split() if word not in stopwords]


def match_highlighter(query, response, tag="b", css_class="highlight", highlight_stopwords=True):
    wrapping = ("<"+tag+" class="+css_class+">", "</"+tag+">")
    wrap = lambda text: wrapping[0] + text + wrapping[1]
    stop_words = word_filter.stopwords.words("english") * (not highlight_stopwords)
    query_set = set(query_reduction(query, stop_words))
    bold_response = ""
    for word in response.split():
        if any(query_word in word.lower() for query_word in query_set):
            bold_response += wrap(word) + " "
        else:
            bold_response += word + " "
    return bold_response


def snippet_generator(transcript, query, soft_max=100, word_margin=50, bold=True):
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
