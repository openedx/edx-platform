"""
Defines asynchronous celery task for auto-tagging content
"""

import logging

from celery import shared_task
from celery_utils.logged_task import LoggedTask
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import Taxonomy

from xmodule.modulestore.django import modulestore

from . import api

LANGUAGE_TAXONOMY_ID = -1

log = logging.getLogger(__name__)
User = get_user_model()


def _has_taxonomy(taxonomy: Taxonomy, content_object) -> bool:
    """
    Return True if this Taxonomy have some Tag set in the content_object
    """
    _exausted = object()

    content_tags = api.get_content_tags(object_id=content_object, taxonomy_id=taxonomy.id)
    return next(content_tags, _exausted) is not _exausted


def _update_tags(content_object, lang) -> None:
    """
    Update the tags for a content_object.

    If the content_object already have a tag for the language taxonomy, it will be skipped.
    """
    lang_taxonomy = Taxonomy.objects.get(pk=LANGUAGE_TAXONOMY_ID)

    if lang and not _has_taxonomy(lang_taxonomy, content_object):
        tags = api.get_tags(lang_taxonomy)
        lang_tag = next(tag for tag in tags if tag.external_id == lang)
        api.tag_content_object(lang_taxonomy, [lang_tag.id], content_object)


def _delete_tags(content_object) -> None:
    api.delete_object_tags(content_object)


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def update_course_tags(course_key_str: str) -> bool:
    """
    Updates the tags for a Course.

    Params:
        course_key_str (str): identifier of the Course
    """
    try:
        course_key = CourseKey.from_string(course_key_str)

        log.info("Updating tags for Course with id: %s", course_key)

        course = modulestore().get_course(course_key)
        lang = course.language

        _update_tags(course_key, lang)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error updating tags for Course with id: %s. %s", course_key, e)
        return False


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def delete_course_tags(course_key_str: str) -> bool:
    """
    Delete the tags for a Course.

    Params:
        course_key_str (str): identifier of the Course
    """
    try:
        course_key = CourseKey.from_string(course_key_str)

        log.info("Deleting tags for Course with id: %s", course_key)

        _delete_tags(course_key)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error deleting tags for Course with id: %s. %s", course_key, e)
        return False


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def update_xblock_tags(usage_key_str: str) -> bool:
    """
    Updates the tags for a XBlock.

    Params:
        usage_key_str (str): identifier of the XBlock
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)

        log.info("Updating tags for XBlock with id: %s", usage_key)

        if usage_key.course_key.is_course:
            course = modulestore().get_course(usage_key.course_key)
            lang = course.language
        else:
            return False

        _update_tags(usage_key, lang)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error updating tags for XBlock with id: %s. %s", usage_key, e)
        return False


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def delete_xblock_tags(usage_key_str: str) -> bool:
    """
    Delete the tags for a XBlock.

    Params:
        usage_key_str (str): identifier of the XBlock
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)

        log.info("Deleting tags for XBlock with id: %s", usage_key)

        _delete_tags(usage_key)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error deleting tags for XBlock with id: %s. %s", usage_key, e)
        return False
