"""
Content Library Transformer, used to filter course structure per user.
"""
import json
from courseware.access import _has_access_to_course
from courseware.models import StudentModule
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer
from xmodule.library_content_module import LibraryContentModule
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.django import modulestore
from eventtracking import tracker


class ContentLibraryTransformer(BlockStructureTransformer):
    """
    Content Library Transformer Class
    """
    VERSION = 1

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
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureCollectedData)

        Returns:
            dict[UsageKey: dict]
        """
        block_structure.request_xblock_fields('mode')
        block_structure.request_xblock_fields('max_count')

        # For each block check if block is library_content.
        # If library_content add children array to content_library_children field
        for block_key in block_structure.topological_traversal():
            xblock = block_structure.get_xblock(block_key)
            block_structure.set_transformer_block_data(block_key, cls, 'content_library_children', [])
            if getattr(xblock, 'category', None) == 'library_content':
                block_structure.set_transformer_block_data(block_key, cls, 'content_library_children', xblock.children)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info(object)
            block_structure (BlockStructureCollectedData)
        """
        store = modulestore()
        lib_tools = LibraryToolsService(store)

        def build_key(block_type, block_id):
            """
            Helper method to build a BlockUsageLocator for user_info.course_key
            """
            return BlockUsageLocator(user_info.course_key, block_type, block_id)

        def update_selection(selected, children, max_count, mode, location):
            """
            Helper method to update library content selection
            """
            return LibraryContentModule.make_selection(
                selected, children, max_count, mode, location, lib_tools, tracker.emit
            )

        def check_child_removal(block_key):
            """
            Check if selected block should be removed.
            Block is removed if it is part of library_content, but has not been selected
            for current user.
            """
            if block_key not in children:
                return False
            if block_key in children and block_key in selected_children:
                return False
            return True

        children = []
        selected_children = []
        for block_key in block_structure.get_block_keys():
            library_children = block_structure.get_transformer_block_data(block_key, self, 'content_library_children')
            if library_children:
                children.extend(library_children)
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
                        usage_key = build_key(state[0], state[1])
                        if usage_key in library_children:
                            selected.append((state[0], state[1]))

                # update selected
                selected = update_selection(selected, children, max_count, mode, block_key)
                selected_children.extend([build_key(s[0], s[1]) for s in selected])

        # Check and remove all non-selected children from course structure.
        block_structure.remove_block_if(
            check_child_removal
        )
