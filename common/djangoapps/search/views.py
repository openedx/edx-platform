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
