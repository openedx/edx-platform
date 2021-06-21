"""Signal handlers for writing course dates into edx_when."""


from datetime import timedelta, datetime
import datetime
import logging

from cms.djangoapps.contentstore.config.waffle import custom_pls_is_active
from django.dispatch import receiver
from edx_when.api import FIELDS_TO_EXTRACT, set_dates_for_course

from xmodule.util.misc import is_xblock_an_assignment
from openedx.core.lib.graph_traversals import get_children, leaf_filter, traverse_pre_order
from xblock.fields import Scope  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import SelfPacedRelativeDatesConfig
from .utils import spaced_out_sections

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
        if field_name == 'due':
            print("THIS IS THE FIELD ", field)
            print(xblock)
            result[field.name] = field.read_from(xblock)
            continue
        if field.scope == Scope.settings and field.is_set_on(xblock):
            try:
                result[field.name] = field.read_from(xblock)
            except TypeError as exception:
                exception_message = "{message}, Block-location:{location}, Field-name:{field_name}".format(
                    message=str(exception),
                    location=str(xblock.location),
                    field_name=field.name
                )
                raise TypeError(exception_message)  # lint-amnesty, pylint: disable=raise-missing-from
    return result


def _has_assignment_blocks(item):
    """
    Check if a given block contains children that are assignments.
    Assignments have graded, has_score and nonzero weight attributes.
    """
    return any(
        is_xblock_an_assignment(block)
        for block in traverse_pre_order(item, get_children, leaf_filter)
    )


def _gather_graded_items(root, due):  # lint-amnesty, pylint: disable=missing-function-docstring
    items = [root]
    has_non_ora_scored_content = False
    collected_items = []
    while items:
        next_item = items.pop()
        if next_item.graded:
            # Sequentials can be marked as graded, while only containing ungraded problems
            # To handle this case, we can look at the leaf blocks within a sequential
            # and check that they are a graded assignment
            # (if they have graded/has_score attributes and nonzero weight)
            # TODO: Once studio can manually set relative dates, we would need to manually check for them here
            collected_items.append((next_item.location, {'due': due if _has_assignment_blocks(next_item) else None}))
            # TODO: This is pretty gross, and should maybe be configurable in the future,
            # especially if we find ourselves needing more exceptions.
            has_non_ora_scored_content = (
                has_non_ora_scored_content or
                (next_item.has_score and next_item.category != 'openassessment')
            )

        items.extend(next_item.get_children())

    if has_non_ora_scored_content:
        return collected_items
    return []


def extract_dates_from_course(course):
    """
    Extract all dates from the supplied course.
    """
    log.info('Extracting course dates for %s', course.id)

    if course.self_paced and custom_pls_is_active(course.id):
        print("This is self paced ")
        date_items = []
        store = modulestore()
        with store.branch_setting(ModuleStoreEnum.Branch.published_only, course.id):
            items = store.get_items(course.id)
        log.info('Extracting dates from %d items in %s', len(items), course.id)
        print("B4 the items sections")
        # new_fields_to_extract = FIELDS_TO_EXTRACT + ('due_num_weeks',)
        # print("THe new fields to extract ", new_fields_to_extract)
        for item in items:
            metadata = _field_values(FIELDS_TO_EXTRACT, item)
            print("THIS IS THE METADATA ", metadata)
            metadata['due'] = datetime.datetime.now() - metadata['due']
            
            # print("TYPE OF DATES: ", metadata)
            # print("RIGHT NOW, ", datetime.datetime.now())
            # print(metadata['due'])
            # metadata['due'] = datetime.datetime.now() - metadata['due']
            # print('metadata due: ', metadata['due'])
            metadata.pop('due_num_weeks',None)
            # print("THIS IS THE DUE DATE: ", metadata['due'])
            date_items.append((item.location, metadata))
            # date_items.append((item.location, _field_values(FIELDS_TO_EXTRACT, item)))
        print("Here are the date items: ", date_items)

    elif course.self_paced and not custom_pls_is_active(course.id):
        metadata = _field_values(FIELDS_TO_EXTRACT, course)
        # self-paced courses may accidentally have a course due date
        metadata.pop('due', None)
        date_items = [(course.location, metadata)]

        if SelfPacedRelativeDatesConfig.current(course_key=course.id).enabled:
            # Apply the same relative due date to all content inside a section,
            # unless that item already has a relative date set
            for _, section, weeks_to_complete in spaced_out_sections(course):
                section_date_items = []
                print("THESE IS THE WEEKS TO COMPLETE ,", weeks_to_complete)
                for subsection in section.get_children():
                    section_date_items.extend(_gather_graded_items(subsection, weeks_to_complete))

                if section_date_items and section.graded:
                    date_items.append((section.location, weeks_to_complete))
                date_items.extend(section_date_items)
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
