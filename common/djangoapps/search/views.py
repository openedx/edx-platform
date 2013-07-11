from mitxmako.shortcuts import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse

import requests
import json
import nltk.data
import nltk.corpus as word_filter
import enchant
import string
import sorting

CONTENT_TYPES = ("transcript", "problem", "pdf")


def search(request):
    context = {}
    results_string = ""
    if request.GET:
        results_string = find(request)
        context.update({"old_query": request.GET.get('s', "")})
    context.update({"previous": request.GET})
    search_bar = render_to_string("search_templates/search.html", context)
    full_html = render_to_string("search_templates/wrapper.html", {"body": search_bar+results_string})
    return HttpResponse(full_html)


def find(request, database="http://127.0.0.1:9200",
         field="searchable_text", max_result=100):
    get_content = lambda request, content: content+"-index" if request.GET.get(content, False) else None
    query = request.GET.get("s", "*.*")
    page = request.GET.get("page", 1)
    results_per_page = request.GET.get("results", 15)
    index = ",".join(filter(None, [get_content(request, content) for content in CONTENT_TYPES]))
    full_url = "/".join([database, index, "_search?q="+field+":"])
    context = {}
    response = requests.get(full_url+query+"&size="+str(max_result))
    results = json.loads(response._content).get("hits", {"hits": ""})["hits"]
    scores = [entry["_score"] for entry in results]
    data = [entry["_source"] for entry in results]
    #titles = [entry["display_name"] for entry in data]
    titles = [entry["display_name"] for entry in data]
    transcripts = [entry["searchable_text"] for entry in data]
    snippets = [snippet_generator(transcript, query) for transcript in transcripts]
    thumbnails = ["data:image/jpg;base64,"+entry["thumbnail"] for entry in data]
    urls = [get_datum_url(request, datum) for datum in data]
    data = zip(titles, snippets, thumbnails, urls, scores)
    data = sorting.sort(data, request.GET.get("sort", None))
    if len(data) == 0:
        data = [("No results found, please try again", "")]
        context.update({"results": "false"})
    else:
        context.update({"results": "true"})

    correction = spell_check(query)
    results_pages = Paginator(data, results_per_page)

    data = proper_page(results_pages, page)
    context.update({
        "data": data, "next_page": next_link(request, data), "prev_page": prev_link(request, data),
        "search_correction_link": search_correction_link(request, correction),
        "spelling_correction": correction})
    return render_to_string("search_templates/results.html", context)


def get_datum_url(request, datum):
    url = request.environ.get('HTTP_REFERER', "")
    host = request.environ.get("HTTP_HOST", "edx.org")
    trigger = "courseware"
    if trigger in url:
        base = url[:url.find(trigger)+len(trigger)+1]
        return base+datum["url"]
    else:
        return "http://" + host + "/courses/" + datum["course_section"]+"/courseware/" + datum["url"]


def query_reduction(query, stopwords):
    return [word.lower() for word in query.split() if word not in stopwords]


def proper_page(pages, index):
    correct_page = pages.page(1)
    try:
        correct_page = pages.page(index)
    except PageNotAnInteger:
        correct_page = pages.page(1)
    except EmptyPage:
        correct_page = pages.page(pages.num_pages)
    return correct_page


def next_link(request, paginator):
    return request.path+"?s="+request.GET.get("s", "") + \
        "&content=" + request.GET.get("content", "transcript") + "&page="+str(paginator.next_page_number())


def prev_link(request, paginator):
    return request.path+"?s="+request.GET.get("s", "") + \
        "&content=" + request.GET.get("content", "transcript") + "&page="+str(paginator.previous_page_number())


def search_correction_link(request, term, page="1"):
    if term:
        return request.path+"?s="+term+"&page="+page+"&content="+request.GET.get("content", "transcript")
    else:
        return request.path+"?s="+request.GET["s"]+"&page"+page+"&content="+request.GET.get("content", "transcript")


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


def snippet_generator(transcript, query, soft_max=50, word_margin=25, bold=True):
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
    try:
        possible_corrections = [dictionary.suggest(word)[0] for word in words]
    except IndexError:
        return False
    if possible_corrections == words:
        return None
    else:
        return " ".join(possible_corrections)
