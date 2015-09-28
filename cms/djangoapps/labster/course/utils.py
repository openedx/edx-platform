""" Labster Course utils. """
import logging
from urlparse import urlparse

from django.contrib.auth.models import User
from contentstore.utils import add_instructor, remove_all_instructors


log = logging.getLogger(__name__)


def strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'for_branch'):
        key = key.for_branch(None)
    if hasattr(key, 'version_agnostic'):
        key = key.version_agnostic()
    return key


def set_staff(course_key, emails):
    """
    Sets course staff.
    """
    remove_all_instructors(course_key)
    for email in emails:
        try:
            user = User.objects.get(email=email)
            add_instructor(course_key, user, user)
        except User.DoesNotExist:
            log.info('User with email %s does not exist', email)


def contains(parameters, key):
    """
    Returns an index of the found parameters, -1 otherwise.
    """
    for index, param in enumerate(parameters):
        param = param.strip()
        if param.startswith(key):
            return index
    return -1


def get_simulation_id(uri):
    """
    Returns Simulation id extracted from the passed URI.
    """
    return urlparse(uri).path.strip('/').split('/')[-1]


def get_parent_xblock(xblock, child_for='sequential'):
    """
    Find a parent for the xblock.
    """
    while xblock:
        xblock = xblock.get_parent()
        if xblock is None:
            return None
        parent = xblock.get_parent()
        if parent is None:
            return None
        if parent.category == child_for:
            return xblock
