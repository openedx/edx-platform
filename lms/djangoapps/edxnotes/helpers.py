"""
Helper methods related to EdxNotes.
"""
import json
import logging
import markupsafe
import requests
from requests.exceptions import RequestException
from uuid import uuid4
from json import JSONEncoder
from datetime import datetime
from courseware.access import has_access
from courseware.views import get_current_child
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from student.models import anonymous_id_for_user
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from util.date_utils import get_default_time_display
from dateutil.parser import parse as dateutil_parse
from provider.oauth2.models import AccessToken, Client
import oauth2_provider.oidc as oidc
from provider.utils import now
from .exceptions import EdxNotesParseError, EdxNotesServiceUnavailable

log = logging.getLogger(__name__)


class NoteJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder that encode datetime objects to appropriate time strings.
    """
    # pylint: disable=method-hidden
    def default(self, obj):
        if isinstance(obj, datetime):
            return get_default_time_display(obj)
        return json.JSONEncoder.default(self, obj)


def get_id_token(user):
    """
    Generates JWT ID-Token, using or creating user's OAuth access token.
    """
    try:
        client = Client.objects.get(name="edx-notes")
    except Client.DoesNotExist:
        raise ImproperlyConfigured("OAuth2 Client with name 'edx-notes' is not present in the DB")
    try:
        access_token = AccessToken.objects.get(
            client=client,
            user=user,
            expires__gt=now()
        )
    except AccessToken.DoesNotExist:
        access_token = AccessToken(client=client, user=user)
        access_token.save()

    id_token = oidc.id_token(access_token)
    secret = id_token.access_token.client.client_secret
    return id_token.encode(secret)


def get_token_url(course_id):
    """
    Returns token url for the course.
    """
    return reverse("get_token", kwargs={
        "course_id": course_id.to_deprecated_string(),
    })


def send_request(user, course_id, path="", query_string=""):
    """
    Sends a request with appropriate parameters and headers.
    """
    url = get_endpoint(path)
    params = {
        "user": anonymous_id_for_user(user, None),
        "course_id": unicode(course_id).encode("utf-8"),
    }

    if query_string:
        params.update({
            "text": query_string,
        })

    try:
        response = requests.get(
            url,
            headers={
                "x-annotator-auth-token": get_id_token(user)
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
    Reprocess provided `collection(list)`: adds information about ancestor,
    converts "updated" date, sorts the collection in descending order.

    Raises:
        ItemNotFoundError - when appropriate module is not found.
    """

    store = modulestore()
    filtered_collection = list()
    cache = {}
    with store.bulk_operations(course.id):
        for model in collection:
            model.update({
                u"text": markupsafe.escape(model["text"]),
                u"quote": markupsafe.escape(model["quote"]),
                u"updated": dateutil_parse(model["updated"]),
            })
            usage_id = model["usage_id"]
            if usage_id in cache:
                model.update(cache[usage_id])
                filtered_collection.append(model)
                continue

            usage_key = course.id.make_usage_key_from_deprecated_string(usage_id)
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
        'location': item.location.to_deprecated_string(),
        'display_name': item.display_name_with_default,
    }

    if item.category == 'chapter' and item.get_parent():
        course = item.get_parent()
        ancestor_children = [child.to_deprecated_string() for child in course.children]
        item_dict['index'] = ancestor_children.index(item_dict['location'])
    elif item.category == 'vertical':
        item_dict['url'] = reverse("jump_to_id", kwargs={
            "course_id": course.id.to_deprecated_string(),
            "module_id": item.url_name,
        })

    if item.category in ('chapter', 'sequential'):
        item_dict['children'] = [child.to_deprecated_string() for child in item.children]

    return item_dict


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


def get_endpoint(path=""):
    """
    Returns endpoint.
    """
    try:
        url = settings.EDXNOTES_INTERFACE['url']
        if not url.endswith("/"):
            url += "/"

        if path:
            if path.startswith("/"):
                path = path.lstrip("/")
            if not path.endswith("/"):
                path += "/"

        return url + path
    except (AttributeError, KeyError):
        raise ImproperlyConfigured(_("No endpoint was provided for EdxNotes."))


def get_course_position(course_module):
    """
    Return the user's current place in the course.

    If this is the user's first time, leads to COURSE/CHAPTER/SECTION.
    If this isn't the users's first time, leads to COURSE/CHAPTER.

    If there is no current position in the course or chapter, then selects
    the first child.
    """
    urlargs = {'course_id': course_module.id.to_deprecated_string()}
    chapter = get_current_child(course_module, min_depth=1)
    if chapter is None:
        log.debug("No chapter found when loading current position in course")
        return None

    urlargs['chapter'] = chapter.url_name
    if course_module.position is not None:
        return {
            'display_name': chapter.display_name_with_default,
            'url': reverse('courseware_chapter', kwargs=urlargs),
        }

    # Relying on default of returning first child
    section = get_current_child(chapter, min_depth=1)
    if section is None:
        log.debug("No section found when loading current position in course")
        return None

    urlargs['section'] = section.url_name
    return {
        'display_name': section.display_name_with_default,
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
    tab_found = next((True for t in course.tabs if t["type"] == "edxnotes"), False)
    feature_enabled = settings.FEATURES.get("ENABLE_EDXNOTES")

    return (feature_enabled and tab_found) and not is_harvard_notes_enabled(course)


def is_harvard_notes_enabled(course):
    """
    Returns True if Harvard Annotation Tool is enabled for the course,
    False otherwise.

    Checks for 'textannotation', 'imageannotation', 'videoannotation' in the list
    of advanced modules of the course.
    """
    modules = set(['textannotation', 'imageannotation', 'videoannotation'])
    return bool(modules.intersection(course.advanced_modules))
