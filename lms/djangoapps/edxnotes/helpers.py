"""
Helper methods related to EdxNotes.
"""
import json
import requests
import logging
from uuid import uuid4
from courseware.access import has_access
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
log = logging.getLogger(__name__)


def get_token():
    """
    Returns authentication token.
    """
    return None


def get_notes(user, course):
    """
    Returns all notes for the user.
    """
    url = get_endpoint("/annotations")
    response = requests.get(url, params={
        'user': user.username,
        'course_id': unicode(course.id).encode('utf-8'),
    })

    try:
        collection = json.loads(response.content)
    except ValueError:
        return []

    # if collection is empty, just return it.
    if not collection:
        return collection

    store = modulestore()
    filtered_collection = list()
    with store.bulk_operations(course.id):
        for model in collection:
            usage_key = course.id.make_usage_key_from_deprecated_string(model['usage_id'])
            try:
                item = store.get_item(usage_key)
            except ItemNotFoundError:
                log.warning("Module not found: %s", usage_key)
                continue

            if not has_access(user, 'load', item, course_key=course.id):
                continue

            url = get_parent_url(course, store, usage_key)
            model.update({
                u'unit': {
                    u'display_name': item.display_name_with_default,
                    u'url': url,
                }
            })
            filtered_collection.append(model)

    return filtered_collection


def get_parent(store, usage_key):
    """
    Returns parent module for the passed `usage_key`.
    """
    location = store.get_parent_location(usage_key)
    if not location:
        log.warning("Parent location for the module not found: %s", usage_key)
        return
    try:
        return store.get_item(location)
    except ItemNotFoundError:
        log.warning("Parent module not found: %s", location)
        return


def get_parent_url(course, store, usage_key):
    """
    Returns dispay_name and url for the parent module.
    """
    parent = get_parent(store, usage_key)
    if not parent:
        return None
    url = reverse('jump_to', kwargs={
        'course_id': course.id.to_deprecated_string(),
        'location': parent.location.to_deprecated_string(),
    })

    return url


def get_endpoint(path=""):
    """
    Returns endpoint.
    """
    interface = settings.EDXNOTES_INTERFACE if hasattr(settings, 'EDXNOTES_INTERFACE') else False
    if interface and interface.get("url", False):
        url = interface["url"]
        if not url.endswith("/"):
            url += "/"
        if path and not path.startswith("/"):
            path = "/" + path

        return url + "api/v1" + path
    else:
        raise ImproperlyConfigured(_("No endpoint was provided for EdxNotes."))


def generate_uid():
    """
    Generates unique id.
    """
    return uuid4().int  # pylint: disable=no-member


def is_feature_enabled(course):
    """
    Returns True if the edxnotes app is enabled for the course, False otherwise.

    In order for the app to be enabled it must be:
        1) enabled globally via FEATURES.
        2) present in the course tab configuration.
    """
    tab_found = next((True for t in course.tabs if t['type'] == 'edxnotes'), False)
    feature_enabled = settings.FEATURES.get('ENABLE_EDXNOTES')

    return feature_enabled and tab_found
