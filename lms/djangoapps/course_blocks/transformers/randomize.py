"""
Randomize Transformer, used to filter course structure per user.

THIS TRANSFORMER IS CURRENTLY NOT BEING USED. 
Randomize block is not being supported any more and is about to be removed from the platform. 
"""
import json
from courseware.models import StudentModule
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class RandomizeTransformer(BlockStructureTransformer):
    """
    Randomize Transformer Class
    """
    VERSION = 1

    @classmethod
    def _get_chosen_modules(cls, user, course_key, block_key):
        """
        Get list of chosen modules in a randomized block,
        for user.

        Arguments:
            user (User)
            course_key (CourseLocator)
            block_key (BlockUsageLocator)

        Returns:
            list[modules]
        """
        # TODO: Still separate from content library implementation, because
        # there is possibility we may need to handle no entry case differently.
        return StudentModule.objects.filter(
            student=user,
            course_id=course_key,
            module_state_key=block_key,
            state__contains='"choice": '
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
        # For each block check if block is randomize.
        # If randomize add children array to randomize_children field
        for block_key in block_structure.topological_traversal():
            xblock = block_structure.get_xblock(block_key)
            if getattr(xblock, 'category', None) == 'randomize':
                block_structure.set_transformer_block_data(block_key, cls, 'randomize_children', xblock.children)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info(object)
            block_structure (BlockStructureCollectedData)
        """

        def check_child_removal(block_key):
            """
            Check if selected block should be removed.
            Block is removed if it is part of randomized, but has not been chosen
            for current user.
            """
            if block_key not in children:
                return False
            if block_key in children and block_key in chosen_child:
                return False
            return True

        children = []
        chosen_child = []
        for block_key in block_structure.get_block_keys():
            randomize_children = block_structure.get_transformer_block_data(block_key, self, 'randomize_children')
            if randomize_children:
                children.extend(randomize_children)
                # Retrieve "choice" json from LMS MySQL database.
                modules = self._get_chosen_modules(user_info.user, user_info.course_key, block_key)
                for module in modules:
                    module_state = module.state
                    chosen = json.loads(module_state)['choice']
                    # Handling only the case if we have "working" chosen key. 
                    if int(chosen) < len(randomize_children):
                    	chosen_child.append(randomize_children[int(chosen)])

        # Check and remove all non-chosen children from course structure.
        if not user_info.has_staff_access:
            block_structure.remove_block_if(
                check_child_removal
            )
