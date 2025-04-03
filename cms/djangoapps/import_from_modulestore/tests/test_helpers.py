"""
Tests for the import_from_modulestore helper functions.
"""
import ddt
from organizations.models import Organization
from unittest.mock import patch

from lxml import etree

from cms.djangoapps.import_from_modulestore import api
from cms.djangoapps.import_from_modulestore.helpers import ImportClient
from common.djangoapps.student.tests.factories import UserFactory

from openedx.core.djangoapps.content_libraries import api as content_libraries_api
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


@ddt.ddt
class TestImportClient(ModuleStoreTestCase):
    """
    Functional tests for the ImportClient class.
    """

    def setUp(self):
        super().setUp()
        self.library = content_libraries_api.create_library(
            org=Organization.objects.create(name='Organization 1', short_name='org1'),
            slug='lib_1',
            title='Library Org 1',
            description='This is a library from Org 1',
        )
        self.user = UserFactory()
        self.course = CourseFactory.create()
        self.chapter = BlockFactory.create(category='chapter', parent=self.course, display_name='Chapter')
        self.sequential = BlockFactory.create(category='sequential', parent=self.chapter, display_name='Sequential')
        self.vertical = BlockFactory.create(category='vertical', parent=self.sequential, display_name='Vertical')
        self.problem = BlockFactory.create(
            category='problem',
            parent=self.vertical,
            display_name='Problem',
            data="""<problem url_name="" display_name="DisplayName"><optionresponse></optionresponse></problem>""",
        )
        self.video = BlockFactory.create(
            category='video',
            parent=self.vertical,
            display_name='Video',
            data="""<video youtube="1.00:3_yD_cEKoCk" url_name="SampleProblem"/>""",
        )

        self.import_event = api.create_import(
            source_key=self.course.id,
            learning_package_id=self.library.learning_package.id,
            user_id=self.user.id,
        )
        self.parser = etree.XMLParser(strip_cdata=False)

    def test_import_from_staged_content(self):
        expected_imported_xblocks = [self.video, self.problem]
        staged_content = self.import_event.get_staged_content_by_block_usage_id(str(self.chapter.location))
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import=str(self.chapter.location),
            composition_level='xblock',
            override=False
        )

        import_client.import_from_staged_content()

        self.assertEqual(self.library.learning_package.content_set.count(), len(expected_imported_xblocks))

    @patch('cms.djangoapps.import_from_modulestore.helpers.ImportClient._process_import')
    def test_import_from_staged_content_block_not_found(self, mocked_process_import):
        staged_content = self.import_event.get_staged_content_by_block_usage_id(str(self.chapter.location))
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import='block-v1:edX+Demo+2025+type@chapter+block@12345',
            composition_level='xblock',
            override=False
        )

        import_client.import_from_staged_content()

        self.assertTrue(not self.library.learning_package.content_set.count())
        mocked_process_import.assert_not_called()

    @ddt.data('chapter', 'sequential', 'vertical')
    def test_create_container(self, block_lvl):
        container_to_import = getattr(self, block_lvl)
        block_usage_id_to_import = str(container_to_import.location)
        staged_content = self.import_event.get_staged_content_by_block_usage_id(block_usage_id_to_import)
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import=block_usage_id_to_import,
            composition_level='xblock',
            override=False
        )
        import_client.create_container(
            container_to_import.category,
            container_to_import.location.block_id,
            container_to_import.display_name
        )

        self.assertEqual(self.library.learning_package.publishable_entities.count(), 1)

    def test_create_container_with_xblock(self):
        block_usage_id_to_import = str(self.problem.location)
        staged_content = self.import_event.get_staged_content_by_block_usage_id(block_usage_id_to_import)
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import=block_usage_id_to_import,
            composition_level='xblock',
            override=False
        )
        with self.assertRaises(ValueError):
            import_client.create_container(
                self.problem.category,
                self.problem.location.block_id,
                self.problem.display_name
            )

    @ddt.data('chapter', 'sequential', 'vertical')
    def test_process_import_with_complicated_blocks(self, block_lvl):
        container_to_import = getattr(self, block_lvl)
        block_usage_id_to_import = str(container_to_import.location)
        staged_content = self.import_event.get_staged_content_by_block_usage_id(block_usage_id_to_import)
        expected_imported_xblocks = [self.problem, self.video]

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import=block_usage_id_to_import,
            composition_level='xblock',
            override=False
        )
        block_to_import = etree.fromstring(staged_content.olx, parser=self.parser)
        # pylint: disable=protected-access
        result = import_client._process_import(block_usage_id_to_import, block_to_import)

        self.assertEqual(self.library.learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(len(result), len(expected_imported_xblocks))
        self.assertEqual(self.import_event.publishableentityimport_set.count(), len(expected_imported_xblocks))

    @ddt.data('problem', 'video')
    def test_process_import_with_simple_blocks(self, block_type_to_import):
        block_to_import = getattr(self, block_type_to_import)
        block_usage_id_to_import = str(block_to_import.location)
        staged_content = self.import_event.get_staged_content_by_block_usage_id(block_usage_id_to_import)
        expected_imported_xblocks = [block_to_import]
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_id_to_import=block_usage_id_to_import,
            composition_level='xblock',
            override=False
        )

        block_to_import = etree.fromstring(block_to_import.data, parser=self.parser)
        # pylint: disable=protected-access
        result = import_client._process_import(block_usage_id_to_import, block_to_import)

        self.assertEqual(self.library.learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(len(result), len(expected_imported_xblocks))
        self.assertEqual(self.import_event.publishableentityimport_set.count(), len(expected_imported_xblocks))
