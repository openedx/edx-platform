<<<<<<< HEAD
from mitxmako.shortcuts import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from models import SearchResults

import requests
import enchant

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
    data = SearchResults(request, response)
    data.sort_results()
    context.update({"results": data.has_results})
    correction = spell_check(query)
    results_pages = Paginator(data.entries, results_per_page)

    data = proper_page(results_pages, page)
    context.update({
        "data": data, "next_page": next_link(request, data), "prev_page": prev_link(request, data),
        "search_correction_link": search_correction_link(request, correction),
        "spelling_correction": correction})
    return render_to_string("search_templates/results.html", context)


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
=======
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from courseware.courses import get_courses
from courseware.model_data import ModelDataCache
from courseware.module_render import get_module_for_descriptor

from courseware.views import registered_for_course
#import logging
import lxml
import re
import posixpath
import urllib
from os import listdir
from os.path import isfile
from os.path import join


def test(request):
    user = User.objects.prefetch_related("groups").get(id=request.user.id)
    request.user = user

    course_list = get_courses(user, request.META.get('HTTP_HOST'))

    all_modules = [get_module(request, user, course) for course in course_list if registered_for_course(course, user)]
    child_modules = []
    for module in all_modules:
        child_modules.extend(module.get_children())
    bottom_modules = []
    for module in child_modules:
        bottom_modules.extend(module.get_children())
    asset_divs = get_asset_div(convert_to_valid_html(bottom_modules[2].get_html()))
    strings = [get_transcript_directory(lxml.html.tostring(div)) for div in asset_divs]
    search_template = get_template('search.html')
    html = search_template.render(Context({'course_list': strings}))
    return HttpResponse(html)


def get_children(course):
    """Returns the children of a given course"""
    attributes = [child.location for child in course._child_instances]
    return attributes


def convert_to_valid_html(html):
    replacement = {"&lt;": "<", "&gt;": ">", "&#34;": "\"", "&#39;": "'"}
    for i, j in replacement.iteritems():
        html = html.replace(i, j)
    return html


def get_asset_div(html_page):
    return lxml.html.find_class(html_page, "video")


def get_module(request, user, course):
    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course.id, user, course, depth=2)
    course_module = get_module_for_descriptor(user, request, course, model_data_cache, course.id)
    return course_module


def get_youtube_code(module_html):
    youtube_snippet = re.sub(r'(.*?)(1\.0:)(.*?)(,1\.25)(.*)', r'\3', module_html)
    sliced_youtube_code = youtube_snippet[:youtube_snippet.find('\n')]
    return sliced_youtube_code


def get_transcript_directory(module_html):
    directory_snippet = re.sub(r'(.*?)(data-caption-asset-path=\")(.*?)(\">.*)', r'\3', module_html)
    sliced_directory = directory_snippet[:directory_snippet.find('\n')]
    return resolve_to_absolute_path(sliced_directory)


def resolve_to_absolute_path(transcript_directory):
    normalized_path = posixpath.normpath(urllib.unquote(transcript_directory)).lstrip('/')
    return all_transcript_files(normalized_path)


def all_transcript_files(normalized_path):
    files = [transcript for transcript in listdir(normalized_path) if isfile(join(normalized_path, transcript))]
    return files
>>>>>>> Storing current elasticsearch progress
