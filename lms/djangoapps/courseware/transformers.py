"""
Grades Transformer
"""
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory

from openedx.core.lib.block_structure.transformer import BlockStructureTransformer
from . import module_render


class GradesBlockTransformer(BlockStructureTransformer):
    """
    The GradesBlockTransformer collects grading information and stores it on
    the block structure.

    No runtime transformations are performed.

    The following values are stored as xblock_fields on their respective blocks in the
    block structure:

        due: (datetime) when the problem is due.
        graded: (boolean)
        has_score: (boolean)
        weight: (numeric)

    Additionally, the following value is calculated and stored as a transformer_block_field
    for each block:

        max_score: (numeric)
    """
    VERSION = 1
    FIELDS_TO_COLLECT = [u'due', u'graded', u'has_score', u'weight']

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

        cls.collect_max_scores(block_structure)

    @staticmethod
    def _iter_xmodules(block_structure):
        """
        Loop through all the blocks locators in the block structure, and retrieve
        the module (XModule or XBlock) associated with that locator.

        For implementation reasons, we need to pull the max_score from the
        XModule, even though the data is not user specific.  Here we bind the
        data to an AnonymousUser.
        """
        request = RequestFactory().get('/dummy-collect-max-grades')
        request.user = AnonymousUser()
        request.session = {}
        for block_locator in block_structure.post_order_traversal():
            course_id = unicode(block_locator.course_key)
            usage_id = unicode(block_locator)  # pylint: disable=protected-access
            module, __ = module_render.get_module_by_usage_id(request, course_id, usage_id)
            yield module

    @classmethod
    def collect_max_scores(cls, block_structure):
        """
        Collect the `max_score` for every block in the provided `block_structure`.
        """
        for module in cls._iter_xmodules(block_structure):
            cls._collect_max_score(block_structure, module)

    @classmethod
    def _collect_max_score(cls, block_structure, module):
        """
        Collect the `max_score` from the given module, storing it as a
        `transformer_block_field` associated with the `GradesBlockTransformer`.
        """
        score = module.max_score()
        block_structure.set_transformer_block_field(module.location, cls, 'max_score', score)

    def transform(self, block_structure, usage_context):
        """
        Perform no transformations.
        """
        pass
