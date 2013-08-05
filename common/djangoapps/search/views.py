import requests
import logging
import hashlib
import json

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from mitxmako.shortcuts import render_to_response
from django_future.csrf import ensure_csrf_cookie

from courseware.courses import get_course_with_access
from search.models import SearchResults
from search.es_requests import MongoIndexer


CONTENT_TYPES = ("transcript", "problem", "pdf")
log = logging.getLogger("mitx.courseware")


@ensure_csrf_cookie
def search(request, course_id):
    """
    Returns search results within course_id from request.

    Request should contain the query string in the "s" parameter.
    """

    course = get_course_with_access(request.user, course_id, 'load')
    context = find(request, course_id)
    context.update({"course": course})
    return render_to_response("search_templates/results.html", context)


@ensure_csrf_cookie
def index_course(request):
    """
    Indexes the searchable material currently within the course

    Is called via AJAX from Studio, and doesn't render any templates.
    """
    indexer = MongoIndexer()
    if "type_id" in request.POST.keys():
        indexer.index_course(request.POST["type_id"])
        return HttpResponse(status=204)
    else:
        return HttpResponseBadRequest()


def find(request, course_id):
    """
    Method in charge of getting search results and associated metadata
    """
    database = settings.ES_DATABASE
    full_query_data = {}
    get_content = lambda request, content: content + "-index" if request.GET.get(content, False) else None
    query = request.GET.get("s", "*.*")
    full_query_data.update(
        {
        "query":
            {"query_string":
                {
                "default_field": "searchable_text",
                "query": query,
                "analyzer": "whitespace"
                }
            }
        }
    )
    index = ",".join(filter(None, [get_content(request, content) for content in CONTENT_TYPES]))
    log.debug(index)
    if len(index) == 0:
        log.debug("Here")
        index = ",".join([content + "-index" for content in CONTENT_TYPES])
    if request.GET.get("all_courses" == "true", False):
        log.debug("no, here")
        base_url = "/".join([database, index])
    else:
        course_hash = hashlib.sha1(course_id).hexdigest()
        base_url = "/".join([database, index, course_hash])
    base_url += "/_search"
    log.debug(base_url)
    log.debug(query)
    # full_query_data.update({"from": 0, "size": 10000})
    full_query_data.update(
        {"suggest": {
            "text": query,
            "simple_phrase": {
                "phrase": {
                    "field": "searchable_text",
                    "size": "4",
                    "max_errors": "2",
                    "real_word_error_likelihood": "0.99",
                }
            }
        }
    })
    log.debug(full_query_data)
    context = {}
    response = requests.get(base_url, data=json.dumps(full_query_data))
    log.debug(response.content)
    data = SearchResults(response, **request.GET)
    data.filter_and_sort()
    context.update({"results": len(data) > 0})
    correction = spell_check(response.content)
    if correction == query:
        correction = ""
    context.update({
        "data": data,
        "old_query": query,
        "search_correction_link": search_correction_link(request, correction),
        "spelling_correction": correction,
        "selected_course": request.GET.get("selected_course", ""),
        "selected_org": request.GET.get("selected_org", "")
    })
    return context


def query_reduction(query, stopwords):
    """
    Reduces full query string to a split list of non stopwords

    Stop words are words with little semantic meaning (a, an, and, etc...)
    that are filtered from the initial search to increase relevancy
    """
    return [word.lower() for word in query.split() if word not in stopwords]


def search_correction_link(request, term, page="1"):
    """
    Generates a link to a version of the query with a corrected search term
    """
    if not term:
        term = request.GET["s"]
    return request.path + "?s=" + term + "&page=" + page + "&content=" + request.GET.get("content", "transcript")


def spell_check(es_response):
    """
    Returns corrected version with attached html if there are suggested corrections.
    """
    suggestions = json.loads(es_response)["suggest"]["searchable_text_suggestions"]
    hits = json.loads(es_response)["hits"].get("total", 0)
    correction = [[entry["text"] if entry["freq"] > 0.1*hits else [] for entry in term["options"]] for term in suggestions]
    true_correction = [correction[i] or [suggestions[i]["text"]] for i in xrange(len(correction))]
    return " ".join(attempt[0] for attempt in true_correction)
