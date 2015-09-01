from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class StudentViewTransformer(BlockStructureTransformer):
    """
    ...
    """
    VERSION = 1
    STUDENT_VIEW_DATA = 'student_view_data'
    STUDENT_VIEW_MULTI_DEVICE = 'student_view_multi_device'

    def __init__(self, requested_student_view_data):
        self.requested_student_view_data = requested_student_view_data

    @classmethod
    def collect(cls, block_structure):
        """
        Collect student_view_multi_device and student_view_data values for each block
        """
        # TODO
        # File "/edx/app/edxapp/edx-platform/common/lib/xmodule/xmodule/x_module.py", line 1125, in _xmodule
        #     raise UndefinedContext()

        # for block_key in block_structure.topological_traversal():
        #     block = block_structure.get_xblock(block_key)
        #     block_structure.set_transformer_block_data(
        #         block_key,
        #         cls,
        #         cls.STUDENT_VIEW_MULTI_DEVICE,
        #         block.has_support(getattr(block, 'student_view', None), 'multi_device'),
        #     )
        #     if getattr(block, 'student_view_data', None):
        #         block_structure.set_transformer_block_data(
        #             block_key,
        #             cls,
        #             cls.STUDENT_VIEW_DATA,
        #             block.student_view_data(),
        #         )

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        for block_key in block_structure.post_order_traversal():
            if block_structure.get_xblock_field(block_key, 'type') not in self.requested_student_view_data:
                block_structure.remove_transformer_block_data(block_key, self, self.STUDENT_VIEW_DATA)
