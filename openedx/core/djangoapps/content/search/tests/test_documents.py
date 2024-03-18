"""
Tests for the Studio content search documents (what gets stored in the index)
"""
from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, ToyCourseFactory

from ..documents import searchable_doc_for_course_block

STUDIO_SEARCH_ENDPOINT_URL = "/api/content_search/v2/studio/"


@skip_unless_cms
class StudioDocumentsTest(SharedModuleStoreTestCase):
    """
    Tests for the Studio content search documents (what gets stored in the
    search index)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = modulestore()
        cls.toy_course = ToyCourseFactory.create()  # See xmodule/modulestore/tests/sample_courses.py
        cls.toy_course_key = cls.toy_course.id
        # Create a problem in library
        cls.problem_block = BlockFactory.create(
            category="problem",
            parent_location=cls.toy_course_key.make_usage_key("vertical", "vertical_test"),
            display_name='Test Problem',
            data="<problem>What is a test?<multiplechoiceresponse></multiplechoiceresponse></problem>",
        )

    def setUp(self):
        super().setUp()

    def test_problem_block(self):
        """
        Test how a problem block gets represented in the search index
        """
        # block_usage_key = self.toy_course_key.make_usage_key("problem", "test_problem")
        block = self.store.get_item(self.problem_block.usage_key)
        doc = searchable_doc_for_course_block(block)
        assert doc == {
            # Note the 'id' has been stripped of special characters to meet Meilisearch requirements.
            # The '-8516ed8' suffix is deterministic based on the original usage key.
            "id": "block-v1edxtoy2012_falltypeproblemblocktest_problem-8516ed8",
            "type": "course_block",
            "block_type": "problem",
            "usage_key": "block-v1:edX+toy+2012_Fall+type@problem+block@Test_Problem",
            "block_id": "Test_Problem",
            "context_key": "course-v1:edX+toy+2012_Fall",
            "org": "edX",
            "display_name": "Test Problem",
            "breadcrumbs": [
                {"display_name": "Toy Course"},
                {"display_name": "chapter"},
                {"display_name": "sequential"},
                {"display_name": "vertical"},
            ],
            "content": {
                "capa_content": "What is a test?",
                "problem_types": ["multiplechoiceresponse"],
            },
        }
