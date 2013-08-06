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
                "analyzer": "standard"
                }
            }
        }
    )
    index = ",".join(filter(None, [get_content(request, content) for content in CONTENT_TYPES]))
    log.debug(index)
    if len(index) == 0:
        index = ",".join([content + "-index" for content in CONTENT_TYPES])
    if request.GET.get("all_courses" == "true", False):
        base_url = "/".join([database, index])
    else:
        course_hash = hashlib.sha1(course_id).hexdigest()
        base_url = "/".join([database, index, course_hash])
    base_url += "/_search"
    log.debug(base_url)
    log.debug(query)
    log.debug(full_query_data)
    context = {}
    response = requests.get(base_url, data=json.dumps(full_query_data))
    log.debug(response.content)
    data = SearchResults(response, **request.GET)
    data.filter_and_sort()
    context.update({"results": len(data) > 0})
    context.update({
        "data": data,
        "old_query": query,
        "selected_course": request.GET.get("selected_course", ""),
        "selected_org": request.GET.get("selected_org", "")
    })
    return context
