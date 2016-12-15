"""
Helper methods related to EdxNotes.
"""

import json
import logging
from json import JSONEncoder
from uuid import uuid4

import requests
from datetime import datetime
from dateutil.parser import parse as dateutil_parse
from opaque_keys.edx.keys import UsageKey
from requests.exceptions import RequestException

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from edxnotes.exceptions import EdxNotesParseError, EdxNotesServiceUnavailable
from capa.util import sanitize_html
from courseware.views import get_current_child
from courseware.access import has_access
from openedx.core.lib.token_utils import get_id_token
from student.models import anonymous_id_for_user
from util.date_utils import get_default_time_display
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger(__name__)
HIGHLIGHT_TAG = "span"
HIGHLIGHT_CLASS = "note-highlight"
# OAuth2 Client name for edxnotes
CLIENT_NAME = "edx-notes"


class NoteJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder that encode datetime objects to appropriate time strings.
    """
    # pylint: disable=method-hidden
    def default(self, obj):
        if isinstance(obj, datetime):
            return get_default_time_display(obj)
        return json.JSONEncoder.default(self, obj)


def get_edxnotes_id_token(user):
    """
    Returns generated ID Token for edxnotes.
    """
    return get_id_token(user, CLIENT_NAME)


def get_token_url(course_id):
    """
    Returns token url for the course.
    """
    return reverse("get_token", kwargs={
        "course_id": unicode(course_id),
    })


def send_request(user, course_id, path="", query_string=None):
    """
    Sends a request with appropriate parameters and headers.
    """
    url = get_internal_endpoint(path)
    params = {
        "user": anonymous_id_for_user(user, None),
        "course_id": unicode(course_id).encode("utf-8"),
    }

    if query_string:
        params.update({
            "text": query_string,
            "highlight": True,
            "highlight_tag": HIGHLIGHT_TAG,
            "highlight_class": HIGHLIGHT_CLASS,
        })

    try:
        response = requests.get(
            url,
            headers={
                "x-annotator-auth-token": get_edxnotes_id_token(user)
            },
            params=params
        )
    except RequestException:
        raise EdxNotesServiceUnavailable(_("EdxNotes Service is unavailable. Please try again in a few minutes."))

    return response


def get_parent_unit(xblock):
    """
    Find vertical that is a unit, not just some container.
    """
    while xblock:
        xblock = xblock.get_parent()
        if xblock is None:
            return None
        parent = xblock.get_parent()
        if parent is None:
            return None
        if parent.category == 'sequential':
            return xblock


def preprocess_collection(user, course, collection):
    """
    Prepare `collection(notes_list)` provided by edx-notes-api
    for rendering in a template:
       add information about ancestor blocks,
       convert "updated" to date

    Raises:
        ItemNotFoundError - when appropriate module is not found.
    """
    # pylint: disable=too-many-statements

    store = modulestore()
    filtered_collection = list()
    cache = {}
    with store.bulk_operations(course.id):
        for model in collection:
            update = {
                u"text": sanitize_html(model["text"]),
                u"quote": sanitize_html(model["quote"]),
                u"updated": dateutil_parse(model["updated"]),
            }
            if "tags" in model:
                update[u"tags"] = [sanitize_html(tag) for tag in model["tags"]]
            model.update(update)
            usage_id = model["usage_id"]
            if usage_id in cache:
                model.update(cache[usage_id])
                filtered_collection.append(model)
                continue

            usage_key = UsageKey.from_string(usage_id)
            # Add a course run if necessary.
            usage_key = usage_key.replace(course_key=store.fill_in_run(usage_key.course_key))

            try:
                item = store.get_item(usage_key)
            except ItemNotFoundError:
                log.debug("Module not found: %s", usage_key)
                continue

            if not has_access(user, "load", item, course_key=course.id):
                log.debug("User %s does not have an access to %s", user, item)
                continue

            unit = get_parent_unit(item)
            if unit is None:
                log.debug("Unit not found: %s", usage_key)
                continue

            section = unit.get_parent()
            if not section:
                log.debug("Section not found: %s", usage_key)
                continue
            if section in cache:
                usage_context = cache[section]
                usage_context.update({
                    "unit": get_module_context(course, unit),
                })
                model.update(usage_context)
                cache[usage_id] = cache[unit] = usage_context
                filtered_collection.append(model)
                continue

            chapter = section.get_parent()
            if not chapter:
                log.debug("Chapter not found: %s", usage_key)
                continue
            if chapter in cache:
                usage_context = cache[chapter]
                usage_context.update({
                    "unit": get_module_context(course, unit),
                    "section": get_module_context(course, section),
                })
                model.update(usage_context)
                cache[usage_id] = cache[unit] = cache[section] = usage_context
                filtered_collection.append(model)
                continue

            usage_context = {
                "unit": get_module_context(course, unit),
                "section": get_module_context(course, section),
                "chapter": get_module_context(course, chapter),
            }
            model.update(usage_context)
            cache[usage_id] = cache[unit] = cache[section] = cache[chapter] = usage_context
            filtered_collection.append(model)

    return filtered_collection


def get_module_context(course, item):
    """
    Returns dispay_name and url for the parent module.
    """
    item_dict = {
        'location': unicode(item.location),
        'display_name': item.display_name_with_default_escaped,
    }
    if item.category == 'chapter' and item.get_parent():
        # course is a locator w/o branch and version
        # so for uniformity we replace it with one that has them
        course = item.get_parent()
        item_dict['index'] = get_index(item_dict['location'], course.children)
    elif item.category == 'vertical':
        section = item.get_parent()
        chapter = section.get_parent()
        # Position starts from 1, that's why we add 1.
        position = get_index(unicode(item.location), section.children) + 1
        item_dict['url'] = reverse('courseware_position', kwargs={
            'course_id': unicode(course.id),
            'chapter': chapter.url_name,
            'section': section.url_name,
            'position': position,
        })
    if item.category in ('chapter', 'sequential'):
        item_dict['children'] = [unicode(child) for child in item.children]

    return item_dict


def get_index(usage_key, children):
    """
    Returns an index of the child with `usage_key`.
    """
    children = [unicode(child) for child in children]
    return children.index(usage_key)


def search(user, course, query_string):
    """
    Returns search results for the `query_string(str)`.
    """
    response = send_request(user, course.id, "search", query_string)
    try:
        content = json.loads(response.content)
        collection = content["rows"]
    except (ValueError, KeyError):
        log.warning("invalid JSON: %s", response.content)
        raise EdxNotesParseError(_("Server error. Please try again in a few minutes."))

    content.update({
        "rows": preprocess_collection(user, course, collection)
    })

    return json.dumps(content, cls=NoteJSONEncoder)


def get_notes(user, course):
    """
    Returns all notes for the user.
    """
    response = send_request(user, course.id, "annotations")
    try:
        collection = json.loads(response.content)
    except ValueError:
        return None

    if not collection:
        return None

    return json.dumps(preprocess_collection(user, course, collection), cls=NoteJSONEncoder)


def get_endpoint(api_url, path=""):
    """
    Returns edx-notes-api endpoint.

    Arguments:
        api_url (str): base url to the notes api
        path (str): path to the resource
    Returns:
        str: full endpoint to the notes api
    """
    try:
        if not api_url.endswith("/"):
            api_url += "/"

        if path:
            if path.startswith("/"):
                path = path.lstrip("/")
            if not path.endswith("/"):
                path += "/"

        return api_url + path
    except (AttributeError, KeyError):
        raise ImproperlyConfigured(_("No endpoint was provided for EdxNotes."))


def get_public_endpoint(path=""):
    """Get the full path to a resource on the public notes API."""
    return get_endpoint(settings.EDXNOTES_PUBLIC_API, path)


def get_internal_endpoint(path=""):
    """Get the full path to a resource on the private notes API."""
    return get_endpoint(settings.EDXNOTES_INTERNAL_API, path)


def get_course_position(course_module):
    """
    Return the user's current place in the course.

    If this is the user's first time, leads to COURSE/CHAPTER/SECTION.
    If this isn't the users's first time, leads to COURSE/CHAPTER.

    If there is no current position in the course or chapter, then selects
    the first child.
    """
    urlargs = {'course_id': unicode(course_module.id)}
    chapter = get_current_child(course_module, min_depth=1)
    if chapter is None:
        log.debug("No chapter found when loading current position in course")
        return None

    urlargs['chapter'] = chapter.url_name
    if course_module.position is not None:
        return {
            'display_name': chapter.display_name_with_default_escaped,
            'url': reverse('courseware_chapter', kwargs=urlargs),
        }

    # Relying on default of returning first child
    section = get_current_child(chapter, min_depth=1)
    if section is None:
        log.debug("No section found when loading current position in course")
        return None

    urlargs['section'] = section.url_name
    return {
        'display_name': section.display_name_with_default_escaped,
        'url': reverse('courseware_section', kwargs=urlargs)
    }


def generate_uid():
    """
    Generates unique id.
    """
    return uuid4().int  # pylint: disable=no-member


def is_feature_enabled(course):
    """
    Returns True if Student Notes feature is enabled for the course,
    False otherwise.

    In order for the application to be enabled it must be:
        1) enabled globally via FEATURES.
        2) present in the course tab configuration.
        3) Harvard Annotation Tool must be disabled for the course.
    """
    return (settings.FEATURES.get("ENABLE_EDXNOTES")
            and [t for t in course.tabs if t["type"] == "edxnotes"]  # tab found
            and not is_harvard_notes_enabled(course))


def is_harvard_notes_enabled(course):
    """
    Returns True if Harvard Annotation Tool is enabled for the course,
    False otherwise.

    Checks for 'textannotation', 'imageannotation', 'videoannotation' in the list
    of advanced modules of the course.
    """
    modules = set(['textannotation', 'imageannotation', 'videoannotation'])
    return bool(modules.intersection(course.advanced_modules))
