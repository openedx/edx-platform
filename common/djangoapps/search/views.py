"""
View functions and interface for search functionality
"""

import logging
import hashlib
import json
import math

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from mitxmako.shortcuts import render_to_response
from django_future.csrf import ensure_csrf_cookie

from courseware.courses import get_course_with_access
from search.models import SearchResults
from search.es_requests import MongoIndexer


CONTENT_TYPES = set(["transcript", "problem"])
FILTER_TYPES = set(["all", "video", "problem"])
RESULTS_PER_PAGE = 10
PAGE_PRELOAD_SPAN = 2
log = logging.getLogger(__name__)


@ensure_csrf_cookie
def search(request, course_id):
    """
    Returns search results within course_id from request.

    Request should contain the query string in the "s" parameter.

    If user doesn't have access to the course, get_course_with_access automatically 404s
    """

    page = int(request.GET.get("page", 1))
    current_filter = request.GET.get("filter", "all")
    course = get_course_with_access(request.user, course_id, 'load')
    search_results = _find(request, course_id)
    full_context = {
        "search_results": _construct_search_context(search_results, page, current_filter),
        "course": course,
        "old_query": request.GET.get("s", "*.*"),
        "course_id": course_id,
        "current_filter": current_filter,
        "page": page
    }
    return render_to_response("search_templates/results.html", full_context)


@ensure_csrf_cookie
def index_course(request):
    """
    Indexes the searchable material currently within the course

    Is called via AJAX from Studio, and doesn't render any templates.
    """

    indexer = MongoIndexer()
    if "course" in request.POST:
        indexer.index_course(request.POST["course"])
        return HttpResponse(status=204)
    else:
        return HttpResponseBadRequest()


def _find(request, course_id):
    """
    Method in charge of getting search results and associated metadata
    """

    database = settings.ES_DATABASE
    query = request.GET.get("s", "*.*")
    full_query_data = \
        {
            "query": {
                "query_string": {
                    "default_field": "searchable_text",
                    "query": query,
                    "analyzer": "standard"
                },
            },
            "size": "1000"
        }
    index = ",".join([content + "-index" for content in CONTENT_TYPES])

    course_hash = hashlib.sha1(course_id).hexdigest()
    base_url = "/".join([database, index, course_hash])
    base_url += "/_search"
    response = requests.get(base_url, data=json.dumps(full_query_data))
    return SearchResults(response, **request.GET)


def _construct_search_context(search_results, page, this_filter):
    """
    Takes the entirety of the results from ElasticSearch and constructs the JSON needed by the template

    Specifically, grabs two pages on either side of the current page within the current filter,
    also associates the total number of results with all other filter types.
    """

    total_results = {filter_: {} for filter_ in FILTER_TYPES}
    functional_results_length = len(search_results.get_category(this_filter))
    total_pages = int(math.ceil(float(functional_results_length) / RESULTS_PER_PAGE))

    current_filter_pages = lambda range_generator: {
        page: search_results.get_page(page, this_filter, RESULTS_PER_PAGE) for page in range_generator
    }

    page_span = xrange(max(1, page - PAGE_PRELOAD_SPAN), min(total_pages + 1, page + PAGE_PRELOAD_SPAN + 1))
    total_results[this_filter]["results"] = current_filter_pages(page_span)
    total_results[this_filter]["total"] = functional_results_length

    results_total = lambda filter_: {
        "total": len(search_results.get_category(filter_)),
        "results": {}
    }

    other_filters = FILTER_TYPES - set([this_filter])
    total_results.update({filter_: results_total(filter_) for filter_ in other_filters})
    return total_results
