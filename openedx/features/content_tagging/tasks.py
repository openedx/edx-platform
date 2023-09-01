"""
Defines asynchronous celery task for auto-tagging content
"""
from __future__ import annotations

import logging

from celery import shared_task
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import Taxonomy

from xmodule.modulestore.django import modulestore

from . import api

LANGUAGE_TAXONOMY_ID = -1

log = logging.getLogger(__name__)
User = get_user_model()


def _has_taxonomy(taxonomy: Taxonomy, content_object: CourseKey | UsageKey) -> bool:
    """
    Return True if this Taxonomy have some Tag set in the content_object
    """
    _exausted = object()

    content_tags = api.get_content_tags(object_id=str(content_object), taxonomy_id=taxonomy.id)
    return next(content_tags, _exausted) is not _exausted


def _set_initial_language_tag(content_object: CourseKey | UsageKey, lang: str) -> None:
    """
    Create a tag for the language taxonomy in the content_object if it doesn't exist.

    If the language is not configured in the plataform or the language tag doesn't exist,
    use the default language of the platform.
    """
    lang_taxonomy = Taxonomy.objects.get(pk=LANGUAGE_TAXONOMY_ID)

    if lang and not _has_taxonomy(lang_taxonomy, content_object):
        tags = api.get_tags(lang_taxonomy)
        is_language_configured = any(lang_code == lang for lang_code, _ in settings.LANGUAGES) is not None
        if not is_language_configured:
            logging.warning(
                "Language not configured in the plataform: %s. Using default language: %s",
                lang,
                settings.LANGUAGE_CODE,
            )
            lang = settings.LANGUAGE_CODE

        lang_tag = next((tag for tag in tags if tag.external_id == lang), None)
        if lang_tag is None:
            if not is_language_configured:
                logging.error(
                    "Language tag not found for default language: %s. Skipping", lang
                )
                return

            logging.warning(
                "Language tag not found for language: %s. Using default language: %s", lang, settings.LANGUAGE_CODE
            )
            lang_tag = next(tag for tag in tags if tag.external_id == settings.LANGUAGE_CODE)

        api.tag_content_object(lang_taxonomy, [lang_tag.id], content_object)


def _delete_tags(content_object: CourseKey | UsageKey) -> None:
    api.delete_object_tags(str(content_object))


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def update_course_tags(course_key_str: str) -> bool:
    """
    Updates the automatically-managed tags for a course
    (whenever a course is created or updated)

    Params:
        course_key_str (str): identifier of the Course
    """
    try:
        course_key = CourseKey.from_string(course_key_str)

        log.info("Updating tags for Course with id: %s", course_key)

        course = modulestore().get_course(course_key)
        if course:
            lang = course.language
            _set_initial_language_tag(course_key, lang)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error updating tags for Course with id: %s. %s", course_key, e)
        return False


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def delete_course_tags(course_key_str: str) -> bool:
    """
    Delete the tags for a Course (when the course itself has been deleted).

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
    Updates the automatically-managed tags for a XBlock
    (whenever an XBlock is created/updated).

    Params:
        usage_key_str (str): identifier of the XBlock
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)

        log.info("Updating tags for XBlock with id: %s", usage_key)

        if usage_key.course_key.is_course:
            course = modulestore().get_course(usage_key.course_key)
            if course is None:
                return True
            lang = course.language
        else:
            return True

        _set_initial_language_tag(usage_key, lang)

        return True
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error updating tags for XBlock with id: %s. %s", usage_key, e)
        return False


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def delete_xblock_tags(usage_key_str: str) -> bool:
    """
    Delete the tags for a XBlock (when the XBlock itself is deleted).

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
