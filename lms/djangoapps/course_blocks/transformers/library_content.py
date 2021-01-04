"""
Content Library Transformer.
"""


import json

import six
from eventtracking import tracker

from lms.djangoapps.courseware.models import StudentModule
from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin
)
from track import contexts
from xmodule.library_content_module import LibraryContentModule
from xmodule.modulestore.django import modulestore

from ..utils import get_student_module_as_dict


class ContentLibraryTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A transformer that manipulates the block structure by removing all
    blocks within a library_content module to which a user should not
    have access.

    Staff users are not to be exempted from library content pathways.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "library_content"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields('mode')
        block_structure.request_xblock_fields('max_count')
        block_structure.request_xblock_fields('category')
        store = modulestore()

        # needed for analytics purposes
        def summarize_block(usage_key):
            """ Basic information about the given block """
            orig_key, orig_version = store.get_block_original_usage(usage_key)
            return {
                "usage_key": six.text_type(usage_key),
                "original_usage_key": six.text_type(orig_key) if orig_key else None,
                "original_usage_version": six.text_type(orig_version) if orig_version else None,
            }

        # For each block check if block is library_content.
        # If library_content add children array to content_library_children field
        for block_key in block_structure.topological_traversal(
                filter_func=lambda block_key: block_key.block_type == 'library_content',
                yield_descendants_of_unyielded=True,
        ):
            xblock = block_structure.get_xblock(block_key)
            for child_key in xblock.children:
                summary = summarize_block(child_key)
                block_structure.set_transformer_block_field(child_key, cls, 'block_analytics_summary', summary)

    def transform_block_filters(self, usage_info, block_structure):
        all_library_children = set()
        all_selected_children = set()
        for block_key in block_structure:
            if block_key.block_type != 'library_content':
                continue
            library_children = block_structure.get_children(block_key)
            if library_children:
                all_library_children.update(library_children)
                selected = []
                mode = block_structure.get_xblock_field(block_key, 'mode')
                max_count = block_structure.get_xblock_field(block_key, 'max_count')

                # Retrieve "selected" json from LMS MySQL database.
                state_dict = get_student_module_as_dict(usage_info.user, usage_info.course_key, block_key)
                for selected_block in state_dict.get('selected', []):
                    # Add all selected entries for this user for this
                    # library module to the selected list.
                    block_type, block_id = selected_block
                    usage_key = usage_info.course_key.make_usage_key(block_type, block_id)
                    if usage_key in library_children:
                        selected.append(selected_block)

                # Update selected
                previous_count = len(selected)
                block_keys = LibraryContentModule.make_selection(selected, library_children, max_count, mode)
                selected = block_keys['selected']

                # Save back any changes
                if any(block_keys[changed] for changed in ('invalid', 'overlimit', 'added')):
                    state_dict['selected'] = list(selected)
                    StudentModule.save_state(
                        student=usage_info.user,
                        course_id=usage_info.course_key,
                        module_state_key=block_key,
                        defaults={
                            'state': json.dumps(state_dict),
                        },
                    )

                # publish events for analytics
                self._publish_events(
                    block_structure,
                    block_key,
                    previous_count,
                    max_count,
                    block_keys,
                    usage_info.user.id,
                )
                all_selected_children.update(usage_info.course_key.make_usage_key(s[0], s[1]) for s in selected)

        def check_child_removal(block_key):
            """
            Return True if selected block should be removed.

            Block is removed if it is part of library_content, but has
            not been selected for current user.
            """
            if block_key not in all_library_children:
                return False
            if block_key in all_selected_children:
                return False
            return True

        return [block_structure.create_removal_filter(check_child_removal)]

    def _publish_events(self, block_structure, location, previous_count, max_count, block_keys, user_id):
        """
        Helper method to publish events for analytics purposes
        """

        def format_block_keys(keys):
            """
            Helper function to format block keys
            """
            json_result = []
            for key in keys:
                info = block_structure.get_transformer_block_field(
                    key, ContentLibraryTransformer, 'block_analytics_summary'
                )
                json_result.append(info)
            return json_result

        def publish_event(event_name, result, **kwargs):
            """
            Helper function to publish an event for analytics purposes
            """
            event_data = {
                "location": six.text_type(location),
                "previous_count": previous_count,
                "result": result,
                "max_count": max_count,
            }
            event_data.update(kwargs)
            context = contexts.course_context_from_course_id(location.course_key)
            if user_id:
                context['user_id'] = user_id
            full_event_name = "edx.librarycontentblock.content.{}".format(event_name)
            with tracker.get_tracker().context(full_event_name, context):
                tracker.emit(full_event_name, event_data)

        LibraryContentModule.publish_selected_children_events(
            block_keys,
            format_block_keys,
            publish_event,
        )
