"""
Tests for the import_from_modulestore helper functions.
"""
import ddt
from organizations.models import Organization
from unittest import mock
from unittest.mock import patch

from lxml import etree
from openedx_learning.api.authoring_models import LearningPackage

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
        self.learning_package = LearningPackage.objects.get(id=self.library.learning_package_id)
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
        with self.captureOnCommitCallbacks(execute=True):
            self.import_event = api.stage_content_for_import(source_key=self.course.id, user_id=self.user.id)
        self.parser = etree.XMLParser(strip_cdata=False)

    def test_import_from_staged_content(self):
        expected_imported_xblocks = [self.video, self.problem]
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=str(self.chapter.location),
            composition_level='xblock',
            override=False
        )

        import_client.import_from_staged_content()

        self.assertEqual(self.learning_package.content_set.count(), len(expected_imported_xblocks))

    @patch('cms.djangoapps.import_from_modulestore.helpers.ImportClient._process_import')
    def test_import_from_staged_content_block_not_found(self, mocked_process_import):
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import='block-v1:edX+Demo+2025+type@chapter+block@12345',
            composition_level='xblock',
            override=False
        )

        import_client.import_from_staged_content()

        self.assertTrue(not self.learning_package.content_set.count())
        mocked_process_import.assert_not_called()

    @ddt.data(
        'chapter',
        'sequential',
        'vertical'
    )
    def test_create_container(self, block_lvl):
        container_to_import = getattr(self, block_lvl)
        block_usage_key_to_import = str(container_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content_for_import.staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=False
        )
        import_client.get_or_create_container(
            container_to_import.category,
            container_to_import.location.block_id,
            container_to_import.display_name,
            str(container_to_import.location)
        )

        self.assertEqual(self.learning_package.publishable_entities.count(), 1)

    def test_create_container_with_xblock(self):
        block_usage_key_to_import = str(self.problem.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content_for_import.staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=False
        )
        with self.assertRaises(ValueError):
            import_client.get_or_create_container(
                self.problem.category,
                self.problem.location.block_id,
                self.problem.display_name,
                str(self.problem.location),
            )

    @ddt.data('chapter', 'sequential', 'vertical')
    def test_process_import_with_complicated_blocks(self, block_lvl):
        container_to_import = getattr(self, block_lvl)
        block_usage_key_to_import = str(container_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content
        expected_imported_xblocks = [self.problem, self.video]

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            block_usage_key_to_import=block_usage_key_to_import,
            target_learning_package=self.learning_package,
            composition_level='xblock',
            override=False
        )
        block_to_import = etree.fromstring(staged_content.olx, parser=self.parser)
        # pylint: disable=protected-access
        result = import_client.import_from_staged_content()

        self.assertEqual(self.learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(len(result), len(expected_imported_xblocks))

    @ddt.data('problem', 'video')
    def test_process_import_with_simple_blocks(self, block_type_to_import):
        block_to_import = getattr(self, block_type_to_import)
        block_usage_key_to_import = str(block_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        expected_imported_xblocks = [block_to_import]
        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content_for_import.staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=False
        )

        block_to_import = etree.fromstring(block_to_import.data, parser=self.parser)
        # pylint: disable=protected-access
        result = import_client._process_import(block_usage_key_to_import, block_to_import)

        self.assertEqual(self.learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(len(result), len(expected_imported_xblocks))

    @ddt.data(True, False)
    def test_process_import_with_override(self, override):
        block_to_import = self.problem
        block_usage_key_to_import = str(block_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content_for_import.staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=False
        )

        block_xml = etree.fromstring(block_to_import.data, parser=self.parser)
        # pylint: disable=protected-access
        result1 = import_client._process_import(block_usage_key_to_import, block_xml)
        self.assertEqual(len(result1), 1)

        with self.captureOnCommitCallbacks(execute=True):
            new_import_event = api.stage_content_for_import(source_key=self.course.id, user_id=self.user.id)

        staged_content_for_import = new_import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        new_staged_content = staged_content_for_import.staged_content
        import_client = ImportClient(
            import_event=new_import_event,
            staged_content=new_staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=override
        )

        if override:
            modified_data = block_to_import.data.replace('DisplayName', 'ModifiedName')
            modified_block = BlockFactory.create(
                category='problem',
                parent=self.vertical,
                display_name='Modified Problem',
                data=modified_data,
            )
            block_xml = etree.fromstring(modified_block.data, parser=self.parser)

            # pylint: disable=protected-access
            result2 = import_client._process_import(block_usage_key_to_import, block_xml)
            self.assertEqual(len(result2), 1)

            assert result2[0].publishable_version.title == 'ModifiedName'
        else:
            # pylint: disable=protected-access
            result2 = import_client._process_import(block_usage_key_to_import, block_xml)
            self.assertEqual(result2, [])

    @patch('cms.djangoapps.import_from_modulestore.helpers.authoring_api')
    def test_container_override(self, mock_authoring_api):
        container_to_import = self.vertical
        block_usage_key_to_import = str(container_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='vertical',
            override=False
        )

        container_version_with_mapping = import_client.get_or_create_container(
            'vertical',
            container_to_import.location.block_id,
            container_to_import.display_name,
            str(container_to_import.location),
        )
        assert container_version_with_mapping is not None
        assert container_version_with_mapping.publishable_version.title == container_to_import.display_name

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='vertical',
            override=True
        )
        container_version_with_mapping = import_client.get_or_create_container(
            'vertical',
            container_to_import.location.block_id,
            'New Display Name',
            str(container_to_import.location),
        )
        overrided_container_version = container_version_with_mapping.publishable_version
        assert overrided_container_version is not None
        assert overrided_container_version.title == 'New Display Name'

    @ddt.data('xblock', 'vertical')
    def test_composition_levels(self, composition_level):
        if composition_level == 'xblock':
            expected_imported_blocks = [self.problem, self.video]
        else:
            # The vertical block is expected to be imported as a container
            # with the same location as the original vertical block.
            expected_imported_blocks = [self.vertical, self.problem, self.video]

        container_to_import = self.vertical
        block_usage_key_to_import = str(container_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level=composition_level,
            override=False
        )

        block_xml = etree.fromstring(staged_content.olx, parser=self.parser)
        # pylint: disable=protected-access
        result = import_client._process_import(block_usage_key_to_import, block_xml)

        self.assertEqual(len(result), len(expected_imported_blocks))

    @patch('cms.djangoapps.import_from_modulestore.helpers.content_staging_api')
    def test_process_staged_content_files(self, mock_content_staging_api):
        block_to_import = self.problem
        block_usage_key_to_import = str(block_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )
        staged_content = staged_content_for_import.staged_content

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='xblock',
            override=False
        )

        mock_file_data = b'file content'
        mock_file = mock.MagicMock()
        mock_file.filename = 'test.png'
        mock_content_staging_api.get_staged_content_static_files.return_value = [mock_file]
        mock_content_staging_api.get_staged_content_static_file_data.return_value = mock_file_data

        modified_data = '<problem url_name="" display_name="ProblemWithImage"><img src="test.png"/></problem>'
        modified_block = BlockFactory.create(
            category='problem',
            parent=self.vertical,
            display_name='Problem With Image',
            data=modified_data,
        )
        block_xml = etree.fromstring(modified_data, parser=self.parser)

        # pylint: disable=protected-access
        import_client._create_block_in_library(block_xml, modified_block.location)
        mock_content_staging_api.get_staged_content_static_file_data.assert_called_once_with(
            staged_content.id, 'test.png'
        )

    def test_update_container_components(self):
        container_to_import = self.vertical
        block_usage_key_to_import = str(container_to_import.location)
        staged_content_for_import = self.import_event.staged_content_for_import.get(
            source_usage_key=self.chapter.location
        )

        import_client = ImportClient(
            import_event=self.import_event,
            staged_content=staged_content_for_import.staged_content,
            target_learning_package=self.learning_package,
            block_usage_key_to_import=block_usage_key_to_import,
            composition_level='container',
            override=False
        )

        with patch('cms.djangoapps.import_from_modulestore.helpers.authoring_api') as mock_authoring_api:
            mock_container_version = mock.MagicMock()
            mock_component_version1 = mock.MagicMock()
            mock_component_version2 = mock.MagicMock()
            mock_component_versions = [mock_component_version1, mock_component_version2]

            # pylint: disable=protected-access
            import_client._update_container_components(mock_container_version, mock_component_versions)

            mock_authoring_api.create_next_container_version.assert_called_once()
            call_args = mock_authoring_api.create_next_container_version.call_args[1]
            self.assertEqual(call_args['container_pk'], mock_container_version.container.pk)
            self.assertEqual(call_args['title'], mock_container_version.title)
            self.assertEqual(call_args['created_by'], self.user.id)
