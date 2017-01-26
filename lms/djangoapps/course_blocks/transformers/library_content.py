"""
Content Library Transformer.
"""
import json
from courseware.models import StudentModule
from openedx.core.lib.block_structure.transformer import BlockStructureTransformer, FilteringTransformerMixin
from xmodule.library_content_module import LibraryContentModule
from xmodule.modulestore.django import modulestore
from eventtracking import tracker


class ContentLibraryTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A transformer that manipulates the block structure by removing all
    blocks within a library_content module to which a user should not
    have access.

    Staff users are *not* exempted from library content pathways.
    """
    VERSION = 1

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
                "usage_key": unicode(usage_key),
                "original_usage_key": unicode(orig_key) if orig_key else None,
                "original_usage_version": unicode(orig_version) if orig_version else None,
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
                module = self._get_student_module(usage_info.user, usage_info.course_key, block_key)
                if module:
                    state_dict = json.loads(module.state)
                    # Add all selected entries for this user for this
                    # library module to the selected list.
                    for state in state_dict['selected']:
                        usage_key = usage_info.course_key.make_usage_key(state[0], state[1])
                        if usage_key in library_children:
                            selected.append((state[0], state[1]))

                # update selected
                previous_count = len(selected)
                block_keys = LibraryContentModule.make_selection(selected, library_children, max_count, mode)
                selected = block_keys['selected']

                # publish events for analytics
                self._publish_events(block_structure, block_key, previous_count, max_count, block_keys)
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

    @classmethod
    def _get_student_module(cls, user, course_key, block_key):
        """
        Get the student module for the given user for the given block.

        Arguments:
            user (User)
            course_key (CourseLocator)
            block_key (BlockUsageLocator)

        Returns:
            StudentModule if exists, or None.
        """
        try:
            return StudentModule.objects.get(
                student=user,
                course_id=course_key,
                module_state_key=block_key,
                state__contains='"selected": [['
            )
        except StudentModule.DoesNotExist:
            return None

    @classmethod
    def _publish_events(cls, block_structure, location, previous_count, max_count, block_keys):
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
                "location": unicode(location),
                "previous_count": previous_count,
                "result": result,
                "max_count": max_count
            }
            event_data.update(kwargs)
            tracker.emit("edx.librarycontentblock.content.{}".format(event_name), event_data)

        LibraryContentModule.publish_selected_children_events(
            block_keys,
            format_block_keys,
            publish_event,
        )
