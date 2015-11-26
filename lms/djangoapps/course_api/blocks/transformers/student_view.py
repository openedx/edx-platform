"""
Student View Transformer
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class StudentViewTransformer(BlockStructureTransformer):
    """
    Only show information that is appropriate for a learner
    """
    VERSION = 1
    STUDENT_VIEW_DATA = 'student_view_data'
    STUDENT_VIEW_MULTI_DEVICE = 'student_view_multi_device'

    def __init__(self, requested_student_view_data=None):
        self.requested_student_view_data = requested_student_view_data or []

    @classmethod
    def name(cls):
        return "blocks_api:student_view"

    @classmethod
    def collect(cls, block_structure):
        """
        Collect student_view_multi_device and student_view_data values for each block
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields('category')

        for block_key in block_structure.topological_traversal():
            block = block_structure.get_xblock(block_key)

            # We're iterating through descriptors (not bound to a user) that are
            # given to us by the modulestore. The reason we look at
            # block.__class__ is to avoid the XModuleDescriptor -> XModule
            # proxying that would happen if we just examined block directly,
            # since it's likely that student_view() is going to be defined on
            # the XModule side.
            #
            # If that proxying happens, this method will throw an
            # UndefinedContext exception, because we haven't initialized any of
            # the user-specific context.
            #
            # This isn't a problem for pure XBlocks, because it's all in one
            # class, and there's no proxying. So basically, if you encounter a
            # problem where your particular XModule explodes here (and don't
            # have the time to convert it to an XBlock), please try refactoring
            # so that you declare your student_view() method in a common
            # ancestor class of both your Descriptor and Module classes. As an
            # example, I changed the name of HtmlFields to HtmlBlock and moved
            # student_view() from HtmlModuleMixin to HtmlBlock.
            student_view = getattr(block.__class__, 'student_view', None)
            supports_multi_device = block.has_support(student_view, 'multi_device')

            block_structure.set_transformer_block_field(
                block_key,
                cls,
                cls.STUDENT_VIEW_MULTI_DEVICE,
                supports_multi_device,
            )
            if getattr(block, 'student_view_data', None):
                student_view_data = block.student_view_data()
                block_structure.set_transformer_block_field(
                    block_key,
                    cls,
                    cls.STUDENT_VIEW_DATA,
                    student_view_data,
                )

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        for block_key in block_structure.post_order_traversal():
            if block_structure.get_xblock_field(block_key, 'category') not in self.requested_student_view_data:
                block_structure.remove_transformer_block_field(block_key, self, self.STUDENT_VIEW_DATA)
