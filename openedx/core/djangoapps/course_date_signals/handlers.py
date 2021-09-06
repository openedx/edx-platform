"""Signal handlers for writing course dates into edx_when."""
from __future__ import absolute_import, unicode_literals

import logging

from django.dispatch import receiver
from six import text_type
from xblock.fields import Scope
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler, modulestore
from .models import SelfPacedRelativeDatesConfig
from .utils import spaced_out_sections
from edx_when.api import FIELDS_TO_EXTRACT, set_dates_for_course

log = logging.getLogger(__name__)


def _field_values(fields, xblock):
    """
    Read field values for the specified fields from the supplied xblock.
    """
    result = {}
    for field_name in fields:
        if field_name not in xblock.fields:
            continue
        field = xblock.fields[field_name]
        if field.scope == Scope.settings and field.is_set_on(xblock):
            try:
                result[field.name] = field.read_from(xblock)
            except TypeError as exception:
                exception_message = "{message}, Block-location:{location}, Field-name:{field_name}".format(
                    message=text_type(exception),
                    location=text_type(xblock.location),
                    field_name=field.name
                )
                raise TypeError(exception_message)
    return result


def extract_dates_from_course(course):
    """
    Extract all dates from the supplied course.
    """
    log.info('Extracting course dates for %s', course.id)
    if course.self_paced:
        metadata = _field_values(FIELDS_TO_EXTRACT, course)
        # self-paced courses may accidentally have a course due date
        metadata.pop('due', None)
        date_items = [(course.location, metadata)]

        if SelfPacedRelativeDatesConfig.current(course_key=course.id).enabled:
            # Apply the same relative due date to all content inside a section,
            # unless that item already has a relative date set
            for _, section, weeks_to_complete in spaced_out_sections(course):
                items = [section]
                while items:
                    next_item = items.pop()
                    if next_item.graded:
                        # TODO: Once studio can manually set relative dates,
                        # we would need to manually check for them here
                        date_items.append((next_item.location, {'due': weeks_to_complete}))
                    items.extend(next_item.get_children())
    else:
        date_items = []
        store = modulestore()
        with store.branch_setting(ModuleStoreEnum.Branch.published_only, course.id):
            items = store.get_items(course.id)
        log.info('Extracting dates from %d items in %s', len(items), course.id)
        for item in items:
            date_items.append((item.location, _field_values(FIELDS_TO_EXTRACT, item)))
    return date_items


@receiver(SignalHandler.course_published)
def extract_dates(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Extract dates from blocks when publishing a course.
    """
    store = modulestore()
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key)

    if not course:
        log.info("No course found for key %s to extract dates from", course_key)
        return

    date_items = extract_dates_from_course(course)

    try:
        set_dates_for_course(course_key, date_items)
    except Exception:  # pylint: disable=broad-except
        log.exception('Unable to set dates for %s on course publish', course_key)
