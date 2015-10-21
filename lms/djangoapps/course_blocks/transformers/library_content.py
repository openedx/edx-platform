"""
Content Library Transformer, used to filter course structure per user.
"""
import json
from courseware.models import StudentModule
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer
from xmodule.library_content_module import LibraryContentModule
from xmodule.modulestore.django import modulestore
from eventtracking import tracker


class ContentLibraryTransformer(BlockStructureTransformer):
    """
    Content Library Transformer Class
    """
    VERSION = 1

    @classmethod
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureCollectedData)
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
            predicate=lambda block_key: block_key.block_type == 'library_content',
            yield_descendants_of_unyielded=True,
        ):
            xblock = block_structure.get_xblock(block_key)
            for child_key in xblock.children:
                summary = summarize_block(child_key)
                block_structure.set_transformer_block_data(child_key, cls, 'block_analytics_summary', summary)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info(object)
            block_structure (BlockStructureCollectedData)
        """

        all_children_of_library_contents = []
        all_selected_children = []
        for block_key in block_structure.topological_traversal(
            predicate=lambda block_key: block_key.block_type == 'library_content',
            yield_descendants_of_unyielded=True,
        ):
            library_children = block_structure.get_children(block_key)
            if library_children:
                all_children_of_library_contents.extend(library_children)
                selected = []
                mode = block_structure.get_xblock_field(block_key, 'mode')
                max_count = block_structure.get_xblock_field(block_key, 'max_count')

                # Retrieve "selected" json from LMS MySQL database.
                modules = self._get_selected_modules(user_info.user, user_info.course_key, block_key)
                for module in modules:
                    module_state = module.state
                    state_dict = json.loads(module_state)
                    # Check all selected entries for this user on selected library.
                    # Add all selected to selected list.
                    for state in state_dict['selected']:
                        usage_key = user_info.course_key.make_usage_key(state[0], state[1])
                        if usage_key in library_children:
                            selected.append((state[0], state[1]))

                # update selected
                previous_count = len(selected)
                block_keys = LibraryContentModule.make_selection(selected, library_children, max_count, mode)
                selected = block_keys['selected']

                # publish events for analytics
                self._publish_events(block_structure, block_key, previous_count, max_count, block_keys)
                all_selected_children.extend([user_info.course_key.make_usage_key(s[0], s[1]) for s in selected])

        def check_child_removal(block_key):
            """
            Check if selected block should be removed.
            Block is removed if it is part of library_content, but has not been selected
            for current user.
            """
            if block_key not in all_children_of_library_contents:
                return False
            if block_key in all_selected_children:
                return False
            return True

        # Check and remove all non-selected children from course structure.
        block_structure.remove_block_if(
            check_child_removal
        )

    @classmethod
    def _get_selected_modules(cls, user, course_key, block_key):
        """
        Get list of selected modules in a library,
        for user.

        Arguments:
            user (User)
            course_key (CourseLocator)
            block_key (BlockUsageLocator)

        Returns:
            list[modules]
        """
        return StudentModule.objects.filter(
            student=user,
            course_id=course_key,
            module_state_key=block_key,
            state__contains='"selected": [['
        )

    @classmethod
    def _publish_events(cls, block_structure, location, previous_count, max_count, block_keys):
        """
        Helper method to publish events for analytics purposes
        """

        def format_block_keys(keys):
            """ Helper method to format block keys """
            json = []
            for key in keys:
                info = block_structure.get_transformer_block_data(
                    key, ContentLibraryTransformer, 'block_analytics_summary'
                )
                json.append(info)
            return json

        def publish_event(event_name, result, **kwargs):
            """ Helper method to publish an event for analytics purposes """
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
