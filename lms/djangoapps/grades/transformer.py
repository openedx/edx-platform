"""
Grades Transformer
"""
from django.test.client import RequestFactory
from functools import reduce as functools_reduce

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from lms.djangoapps.course_blocks.transformers.utils import collect_unioned_set_field, get_field_on_block
from openedx.core.lib.block_structure.transformer import BlockStructureTransformer
from openedx.core.djangoapps.util.user_utils import SystemUser


class GradesTransformer(BlockStructureTransformer):
    """
    The GradesTransformer collects grading information and stores it on
    the block structure.

    No runtime transformations are performed.

    The following values are stored as xblock_fields on their respective blocks
    in the block structure:

        due: (datetime) when the problem is due.
        format: (string) what type of problem it is
        graded: (boolean)
        has_score: (boolean)
        weight: (numeric)

    Additionally, the following value is calculated and stored as a
    transformer_block_field for each block:

        max_score: (numeric)
    """
    VERSION = 4
    FIELDS_TO_COLLECT = [u'due', u'format', u'graded', u'has_score', u'weight', u'course_version', u'subtree_edited_on']

    EXPLICIT_GRADED_FIELD_NAME = 'explicit_graded'

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return u'grades'

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields(*cls.FIELDS_TO_COLLECT)
        cls._collect_max_scores(block_structure)
        collect_unioned_set_field(
            block_structure=block_structure,
            transformer=cls,
            merged_field_name='subsections',
            filter_by=lambda block_key: block_key.block_type == 'sequential',
        )
        cls._collect_explicit_graded(block_structure)

    def transform(self, block_structure, usage_context):
        """
        Perform no transformations.
        """
        pass

    @classmethod
    def _collect_explicit_graded(cls, block_structure):
        """
        Collect the 'explicit_graded' field for every block.
        """
        def _set_field(block_key, field_value):
            """
            Sets the explicit graded field to the given value for the
            given block.
            """
            block_structure.set_transformer_block_field(block_key, cls, cls.EXPLICIT_GRADED_FIELD_NAME, field_value)

        def _get_field(block_key):
            """
            Gets the explicit graded field to the given value for the
            given block.
            """
            return block_structure.get_transformer_block_field(block_key, cls, cls.EXPLICIT_GRADED_FIELD_NAME)

        block_types_to_ignore = {'course', 'chapter', 'sequential'}

        for block_key in block_structure.topological_traversal():
            if block_key.block_type in block_types_to_ignore:
                _set_field(block_key, None)
            else:
                explicit_field_on_block = get_field_on_block(block_structure.get_xblock(block_key), 'graded')
                if explicit_field_on_block is not None:
                    _set_field(block_key, explicit_field_on_block)
                else:
                    values_from_parents = [
                        _get_field(parent)
                        for parent in block_structure.get_parents(block_key)
                        if parent.block_type not in block_types_to_ignore
                    ]
                    non_null_values_from_parents = [value for value in values_from_parents if not None]
                    explicit_from_parents = functools_reduce(lambda x, y: x or y, non_null_values_from_parents, None)
                    _set_field(block_key, explicit_from_parents)

    @classmethod
    def _collect_max_scores(cls, block_structure):
        """
        Collect the `max_score` for every block in the provided `block_structure`.
        """
        for module in cls._iter_scorable_xmodules(block_structure):
            cls._collect_max_score(block_structure, module)

    @classmethod
    def _collect_max_score(cls, block_structure, module):
        """
        Collect the `max_score` from the given module, storing it as a
        `transformer_block_field` associated with the `GradesTransformer`.
        """
        score = module.max_score()
        block_structure.set_transformer_block_field(module.location, cls, 'max_score', score)

    @staticmethod
    def _iter_scorable_xmodules(block_structure):
        """
        Loop through all the blocks locators in the block structure, and
        retrieve the module (XModule or XBlock) associated with that locator.

        For implementation reasons, we need to pull the max_score from the
        XModule, even though the data is not user specific.  Here we bind the
        data to a SystemUser.
        """
        request = RequestFactory().get('/dummy-collect-max-grades')
        user = SystemUser()
        request.user = user
        request.session = {}
        root_block = block_structure.get_xblock(block_structure.root_block_usage_key)
        course_key = block_structure.root_block_usage_key.course_key
        cache = FieldDataCache.cache_for_descriptor_descendents(
            course_id=course_key,
            user=request.user,
            descriptor=root_block,
            descriptor_filter=lambda descriptor: descriptor.has_score,
        )
        for block_locator in block_structure.post_order_traversal():
            block = block_structure.get_xblock(block_locator)
            if getattr(block, 'has_score', False):
                module = get_module_for_descriptor(user, request, block, cache, course_key)
                yield module
