"""
View for Courseware Index
"""

# pylint: disable=attribute-defined-outside-init


import logging

from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.modulestore.django import modulestore

from lms.djangoapps.courseware.exceptions import Redirect
from openedx.features.course_experience.url_helpers import make_learning_mfe_courseware_url

from ..block_render import get_block_for_descriptor

log = logging.getLogger("edx.courseware.views.index")

CONTENT_DEPTH = 2


class CoursewareIndex(View):
    """
    View class for the Courseware page.
    """

    def get(self, request, course_id, chapter=None, section=None, position=None):
        """
        Instead of loading the legacy courseware sequences pages, load the equivalent URL
        in the learning MFE.  This view does not do any auth checks since they are done by
        the MFE when attempting to load content.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
            chapter (unicode): chapter url_name
            section (unicode): section url_name
            position (unicode): position in block, eg of <sequential> block

        """

        course_key = CourseKey.from_string(course_id)

        # Shallow course load to resolve chapters/sections
        store = modulestore()
        course = store.get_course(course_key, depth=CONTENT_DEPTH)

        section_location = None
        if chapter and section:
            chapter_block = course.get_child_by(lambda m: m.location.block_id == chapter)
            if chapter_block:
                section_block = chapter_block.get_child_by(lambda m: m.location.block_id == section)
                if section_block:
                    section_location = section_block.location

        try:
            unit_key = UsageKey.from_string(request.GET.get('activate_block_id', ''))
            if unit_key.block_type != 'vertical':
                unit_key = None
        except InvalidKeyError:
            unit_key = None

        mfe_url = make_learning_mfe_courseware_url(
            course_key,
            section_location,
            unit_key,
            params=request.GET,
            preview=False
        )
        raise Redirect(mfe_url)


def save_child_position(seq_block, child_name):
    """
    child_name: url_name of the child
    """
    for position, child in enumerate(seq_block.get_children(), start=1):
        if child.location.block_id == child_name:
            # Only save if position changed
            if position != seq_block.position:
                seq_block.position = position
    # Save this new position to the underlying KeyValueStore
    seq_block.save()


def save_positions_recursively_up(user, request, field_data_cache, xmodule, course=None):
    """
    Recurses up the course tree starting from a leaf
    Saving the position property based on the previous node as it goes
    """
    current_block = xmodule

    while current_block:
        parent_location = modulestore().get_parent_location(current_block.location)
        parent = None
        if parent_location:
            parent_block = modulestore().get_item(parent_location)
            parent = get_block_for_descriptor(
                user,
                request,
                parent_block,
                field_data_cache,
                current_block.location.course_key,
                course=course
            )

        if parent and hasattr(parent, 'position'):
            save_child_position(parent, current_block.location.block_id)

        current_block = parent
