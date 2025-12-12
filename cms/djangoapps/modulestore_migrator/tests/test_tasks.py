"""
Tests for the modulestore_migrator tasks
"""

from unittest.mock import Mock, patch

import ddt
from django.utils import timezone
from lxml import etree
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Collection, PublishableEntityVersion
from organizations.tests.factories import OrganizationFactory
from user_tasks.models import UserTaskArtifact
from user_tasks.tasks import UserTaskStatus

from cms.djangoapps.modulestore_migrator.data import CompositionLevel, RepeatHandlingStrategy
from cms.djangoapps.modulestore_migrator.models import (
    ModulestoreMigration,
    ModulestoreSource,
)
from cms.djangoapps.modulestore_migrator.tasks import (
    MigrationStep,
    _BulkMigrationTask,
    _migrate_component,
    _migrate_container,
    _migrate_node,
    _MigratedNode,
    _MigrationContext,
    _MigrationTask,
    bulk_migrate_from_modulestore,
    migrate_from_modulestore,
)
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries import api as lib_api
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory


@ddt.ddt
class TestMigrateFromModulestore(ModuleStoreTestCase):
    """
    Test the migrate_from_modulestore task
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.organization = OrganizationFactory(short_name="testorg")
        self.lib_key = LibraryLocatorV2.from_string(
            f"lib:{self.organization.short_name}:test-key"
        )
        self.lib_key_2 = LibraryLocatorV2.from_string(
            f"lib:{self.organization.short_name}:test-key-2"
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key.slug,
            title="Test Library",
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key_2.slug,
            title="Test Library 2",
        )
        self.library = lib_api.ContentLibrary.objects.get(slug=self.lib_key.slug)
        self.library_2 = lib_api.ContentLibrary.objects.get(slug=self.lib_key_2.slug)
        self.learning_package = self.library.learning_package
        self.learning_package_2 = self.library_2.learning_package
        self.course = CourseFactory(
            org=self.organization.short_name,
            course="TestCourse",
            run="TestRun",
            display_name="Test Course",
        )
        self.course_2 = CourseFactory(
            org=self.organization.short_name,
            course="TestCourse2",
            run="TestRun2",
            display_name="Test Course 2",
        )
        self.legacy_library = LibraryFactory(
            org=self.organization.short_name,
            library="LegacyLibrary",
            display_name="Legacy Library",
        )
        self.legacy_library_2 = LibraryFactory(
            org=self.organization.short_name,
            library="LegacyLibrary2",
            display_name="Legacy Library 2",
        )
        self.collection = Collection.objects.create(
            learning_package=self.learning_package,
            key="test_collection",
            title="Test Collection",
        )
        self.collection2 = Collection.objects.create(
            learning_package=self.learning_package,
            key="test_collection2",
            title="Test Collection 2",
        )

    def _get_task_status_fail_message(self, status):
        """
        Helper method to get the failure message from a UserTaskStatus object.
        """
        if status.state == UserTaskStatus.FAILED:
            return UserTaskArtifact.objects.get(status=status, name="Error").text
        return None

    def test_migrate_node_wiki_tag(self):
        """
        Test _migrate_node ignores wiki tags
        """
        wiki_node = etree.fromstring("<wiki />")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result = _migrate_node(
            context=context,
            source_node=wiki_node,
        )

        self.assertIsNone(result.source_to_target)
        self.assertEqual(len(result.children), 0)

    def test_migrate_node_course_root(self):
        """
        Test _migrate_node handles course root
        """
        course_node = etree.fromstring(
            '<course url_name="course" display_name="Test Course">'
            '<chapter url_name="chapter1" display_name="Chapter 1" />'
            "</course>"
        )
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result = _migrate_node(
            context=context,
            source_node=course_node,
        )

        # Course root should not be migrated
        self.assertIsNone(result.source_to_target)
        # But should have children processed
        self.assertEqual(len(result.children), 1)

    def test_migrate_node_library_root(self):
        """
        Test _migrate_node handles library root
        """
        library_node = etree.fromstring(
            '<library url_name="library" display_name="Test Library">'
            '<problem url_name="problem1" display_name="Problem 1" />'
            "</library>"
        )
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )
        result = _migrate_node(
            context=context,
            source_node=library_node,
        )

        # Library root should not be migrated
        self.assertIsNone(result.source_to_target)
        # But should have children processed
        self.assertEqual(len(result.children), 1)

    @ddt.data(
        ("chapter", CompositionLevel.Unit, None),
        ("sequential", CompositionLevel.Unit, None),
        ("vertical", CompositionLevel.Unit, True),
        ("chapter", CompositionLevel.Section, True),
        ("sequential", CompositionLevel.Section, True),
        ("vertical", CompositionLevel.Section, True),
    )
    @ddt.unpack
    def test_migrate_node_container_composition_level(
        self, tag_name, composition_level, should_migrate
    ):
        """
        Test _migrate_node respects composition level for containers
        """
        container_node = etree.fromstring(
            f'<{tag_name} url_name="test_{tag_name}" display_name="Test {tag_name.title()}" />'
        )
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=composition_level,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result = _migrate_node(
            context=context,
            source_node=container_node,
        )

        if should_migrate:
            self.assertIsNotNone(result.source_to_target)
            source_key, _, reason = result.source_to_target
            self.assertEqual(source_key.block_type, tag_name)
            self.assertEqual(source_key.block_id, f"test_{tag_name}")
            self.assertIsNone(reason)
        else:
            self.assertIsNone(result.source_to_target)

    def test_migrate_node_without_url_name(self):
        """
        Test _migrate_node handles nodes without url_name
        """
        node_without_url_name = etree.fromstring(
            '<problem display_name="No URL Name" />'
        )
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result = _migrate_node(
            context=context,
            source_node=node_without_url_name,
        )

        self.assertIsNone(result.source_to_target)
        self.assertEqual(len(result.children), 0)

    def test_migrate_node_with_children_components(self):
        """
        Test _migrate_node handles nodes with children components
        """
        node_without_url_name = etree.fromstring('''
        <library_content display_name="Test lib content" url_name="test_library_content">
        <problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>
        <problem display_name="Test Problem2"><multiplechoiceresponse></multiplechoiceresponse></problem>
        </library_content>
        ''')
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result = _migrate_node(
            context=context,
            source_node=node_without_url_name,
        )

        self.assertEqual(
            result.source_to_target,
            (
                self.course.id.make_usage_key('library_content', 'test_library_content'),
                None,
                'The "library_content" XBlock (ID: "test_library_content") has children, '
                'so it not supported in content libraries. It has 2 children blocks.',
            ),
        )
        self.assertEqual(len(result.children), 0)

    def test_migrated_node_all_source_to_target_pairs(self):
        """
        Test _MigratedNode.all_source_to_target_pairs traversal
        """
        mock_version1 = Mock(spec=PublishableEntityVersion)
        mock_version2 = Mock(spec=PublishableEntityVersion)
        mock_version3 = Mock(spec=PublishableEntityVersion)

        key1 = self.course.id.make_usage_key("problem", "problem1")
        key2 = self.course.id.make_usage_key("problem", "problem2")
        key3 = self.course.id.make_usage_key("problem", "problem3")

        child_node = _MigratedNode(source_to_target=(key3, mock_version3, None), children=[])
        parent_node = _MigratedNode(
            source_to_target=(key1, mock_version1, None),
            children=[
                _MigratedNode(source_to_target=(key2, mock_version2, None), children=[]),
                child_node,
            ],
        )

        pairs = list(parent_node.all_source_to_target_pairs())

        self.assertEqual(len(pairs), 3)
        self.assertEqual(pairs[0][0], key1)
        self.assertEqual(pairs[1][0], key2)
        self.assertEqual(pairs[2][0], key3)

    def test_migrate_from_modulestore_invalid_source(self):
        """
        Test migrate_from_modulestore with invalid source
        """
        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": 999999,  # Non-existent source
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(self._get_task_status_fail_message(status), "ModulestoreSource matching query does not exist.")

    def test_bulk_migrate_invalid_sources(self):
        """
        Test bulk_migrate_from_modulestore with invalid source
        """
        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [999999],  # Non-existent source
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(self._get_task_status_fail_message(status), "ModulestoreSource matching query does not exist.")

    def test_migrate_from_modulestore_invalid_collection(self):
        """
        Test migrate_from_modulestore with invalid collection
        """
        source = ModulestoreSource.objects.create(
            key=self.course.id,
        )

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": 999999,  # Non-existent collection
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(self._get_task_status_fail_message(status), "Collection matching query does not exist.")

    def test_bulk_migrate_invalid_collection(self):
        """
        Test bulk_migrate_from_modulestore with invalid collection
        """
        source = ModulestoreSource.objects.create(
            key=self.course.id,
        )

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [999999],  # Non-existent collection
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(self._get_task_status_fail_message(status), "Collection matching query does not exist.")

    def test_migration_task_calculate_total_steps(self):
        """
        Test _MigrationTask.calculate_total_steps returns correct count
        """
        total_steps = _MigrationTask.calculate_total_steps({})
        expected_steps = len(list(MigrationStep)) - 1
        self.assertEqual(total_steps, expected_steps)

    def test_bulk_migration_task_calculate_total_steps(self):
        """
        Test _BulkMigrationTask.calculate_total_steps returns correct count
        """
        total_steps = _BulkMigrationTask.calculate_total_steps({
            "sources_pks": [1, 2, 3, 4],
        })
        expected_steps = len(list(MigrationStep)) - 1 + 6 * 3
        self.assertEqual(total_steps, expected_steps)

    def test_migrate_component_success(self):
        """
        Test _migrate_component successfully creates a new component
        """
        source_key = self.course.id.make_usage_key("problem", "test_problem")
        olx = '<problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )

        self.assertIsNone(reason)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, PublishableEntityVersion)

        self.assertEqual(
            "problem", result.componentversion.component.component_type.name
        )

        # The component is published
        self.assertFalse(result.componentversion.component.versioning.has_unpublished_changes)

    def test_migrate_component_failure(self):
        """
        Test _migrate_component fails to import component with children
        """
        source_key = self.course.id.make_usage_key("library_content", "test_library_content")
        olx = '''
        <library_content display_name="Test lib content">
        <problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>
        <problem display_name="Test Problem2"><multiplechoiceresponse></multiplechoiceresponse></problem>
        </library_content>
        '''
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_library content"
        )

        self.assertIsNone(result)
        self.assertEqual(
            reason,
            'The "library_content" XBlock (ID: "test_library_content") has children,'
            ' so it not supported in content libraries.',
        )

    def test_migrate_component_with_static_content(self):
        """
        Test _migrate_component with static file content
        """
        source_key = self.course.id.make_usage_key("problem", "test_problem_with_image")
        olx = '<problem display_name="Test Problem"><p>See image: test_image.png</p></problem>'

        media_type = authoring_api.get_or_create_media_type("image/png")
        test_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"fake_image_data",
            created=timezone.now(),
        )
        content_by_filename = {"test_image.png": test_content.id}
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename=content_by_filename,
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )
        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )

        self.assertIsNotNone(result)
        self.assertIsNone(reason)

        component_content = result.componentversion.componentversioncontent_set.filter(
            key="static/test_image.png"
        ).first()
        self.assertIsNotNone(component_content)
        self.assertEqual(component_content.content_id, test_content.id)

    def test_migrate_component_replace_existing_false(self):
        """
        Test _migrate_component with replace_existing=False returns existing component
        """
        source_key = self.course.id.make_usage_key("problem", "existing_problem")
        olx = '<problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, first_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )

        context.existing_source_to_target_keys[source_key] = [first_result.entity]

        second_result, second_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx='<problem display_name="Updated Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>',
            title="updated_problem"
        )
        self.assertIsNone(first_reason)
        self.assertIsNone(second_reason)

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertEqual(first_result.version_num, second_result.version_num)

    def test_migrate_component_same_title(self):
        """
        Test _migrate_component for two components with the same title

        Using preserve_url_slugs=False to create a new component with
        a different URL slug based on the component's Title.
        """
        source_key_1 = self.course.id.make_usage_key("problem", "existing_problem_1")
        source_key_2 = self.course.id.make_usage_key("problem", "existing_problem_2")
        olx = '<problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, first_reason = _migrate_component(
            context=context,
            source_key=source_key_1,
            olx=olx,
            title="test_problem"
        )

        context.existing_source_to_target_keys[source_key_1] = [first_result.entity]

        second_result, second_reason = _migrate_component(
            context=context,
            source_key=source_key_2,
            olx=olx,
            title="test_problem"
        )
        self.assertIsNone(first_reason)
        self.assertIsNone(second_reason)

        self.assertNotEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.entity.key, second_result.entity.key)

    def test_migrate_component_replace_existing_true(self):
        """
        Test _migrate_component with replace_existing=True creates new version
        """
        source_key = self.course.id.make_usage_key("problem", "replaceable_problem")
        original_olx = '<problem display_name="Original"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Update,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, first_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=original_olx,
            title="original"
        )

        context.existing_source_to_target_keys[source_key] = [first_result.entity]

        updated_olx = '<problem display_name="Updated"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        second_result, second_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=updated_olx,
            title="updated"
        )
        self.assertIsNone(first_reason)
        self.assertIsNone(second_reason)

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.version_num, second_result.version_num)

    def test_migrate_component_different_block_types(self):
        """
        Test _migrate_component with different block types
        """
        block_types = ["problem", "html", "video", "discussion"]

        for block_type in block_types:
            source_key = self.course.id.make_usage_key(block_type, f"test_{block_type}")
            olx = f'<{block_type} display_name="Test {block_type.title()}"></{block_type}>'
            context = _MigrationContext(
                existing_source_to_target_keys={},
                target_package_id=self.learning_package.id,
                target_library_key=self.library.library_key,
                source_context_key=self.course.id,
                content_by_filename={},
                composition_level=CompositionLevel.Unit,
                repeat_handling_strategy=RepeatHandlingStrategy.Skip,
                preserve_url_slugs=True,
                created_at=timezone.now(),
                created_by=self.user.id,
            )

            result, reason = _migrate_component(
                context=context,
                source_key=source_key,
                olx=olx,
                title="test"
            )

            self.assertIsNotNone(result, f"Failed to migrate {block_type}")
            self.assertIsNone(reason)

            self.assertEqual(
                block_type, result.componentversion.component.component_type.name
            )

    def test_migrate_component_content_filename_not_in_olx(self):
        """
        Test _migrate_component ignores content files not referenced in OLX
        """
        source_key = self.course.id.make_usage_key(
            "problem", "test_problem_selective_content"
        )
        olx = '<problem display_name="Test Problem"><p>See image: referenced.png</p></problem>'

        media_type = authoring_api.get_or_create_media_type("image/png")
        referenced_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"referenced_image_data",
            created=timezone.now(),
        )
        unreferenced_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"unreferenced_image_data",
            created=timezone.now(),
        )

        content_by_filename = {
            "referenced.png": referenced_content.id,
            "unreferenced.png": unreferenced_content.id,
        }
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename=content_by_filename,
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )

        self.assertIsNotNone(result)
        self.assertIsNone(reason)

        referenced_content_exists = (
            result.componentversion.componentversioncontent_set.filter(
                key="static/referenced.png"
            ).exists()
        )
        unreferenced_content_exists = (
            result.componentversion.componentversioncontent_set.filter(
                key="static/unreferenced.png"
            ).exists()
        )

        self.assertTrue(referenced_content_exists)
        self.assertFalse(unreferenced_content_exists)

    def test_migrate_component_library_source_key(self):
        """
        Test _migrate_component with library source key
        """
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        source_key = library_key.make_usage_key("problem", "library_problem")
        olx = '<problem display_name="Library Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="library_problem"
        )

        self.assertIsNotNone(result)
        self.assertIsNone(reason)

        self.assertEqual(
            "problem", result.componentversion.component.component_type.name
        )

    def test_migrate_component_duplicate_content_integrity_error(self):
        """
        Test _migrate_component handles IntegrityError when content already exists
        """
        source_key = self.course.id.make_usage_key(
            "problem", "test_problem_duplicate_content"
        )
        olx = '<problem display_name="Test Problem"><p>See image: duplicate.png</p></problem>'

        media_type = authoring_api.get_or_create_media_type("image/png")
        test_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"test_image_data",
            created=timezone.now(),
        )
        content_by_filename = {"duplicate.png": test_content.id}
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename=content_by_filename,
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Update,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, first_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )
        self.assertIsNone(first_reason)

        context.existing_source_to_target_keys[source_key] = [first_result.entity]

        second_result, second_reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test_problem"
        )
        self.assertIsNone(second_reason)

        self.assertIsNotNone(first_result)
        self.assertIsNotNone(second_result)
        self.assertEqual(first_result.entity_id, second_result.entity_id)

    def test_migrate_container_creates_new_container(self):
        """
        Test _migrate_container creates a new container when none exists
        """
        source_key = self.course.id.make_usage_key("vertical", "test_vertical")

        child_component_1 = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "problem"
            ),
            local_key="child_problem_1",
            created=timezone.now(),
            created_by=self.user.id,
        )
        child_version_1 = authoring_api.create_next_component_version(
            child_component_1.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )

        child_component_2 = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "html"
            ),
            local_key="child_html_1",
            created=timezone.now(),
            created_by=self.user.id,
        )
        child_version_2 = authoring_api.create_next_component_version(
            child_component_2.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )

        children = [
            child_version_1.publishable_entity_version,
            child_version_2.publishable_entity_version,
        ]
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Test Vertical",
            children=children,
        )

        self.assertIsNone(reason)
        self.assertIsInstance(result, PublishableEntityVersion)

        container_version = result.containerversion
        self.assertEqual(container_version.title, "Test Vertical")

        entity_rows = container_version.entity_list.entitylistrow_set.all()
        self.assertEqual(len(entity_rows), 2)

        child_entity_ids = {row.entity_id for row in entity_rows}
        expected_entity_ids = {child.entity_id for child in children}
        self.assertEqual(child_entity_ids, expected_entity_ids)

    def test_migrate_container_different_container_types(self):
        """
        Test _migrate_container works with different container types
        """
        container_types = [
            (lib_api.ContainerType.Unit, "vertical"),
            (lib_api.ContainerType.Subsection, "sequential"),
            (lib_api.ContainerType.Section, "chapter"),
        ]
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        for container_type, block_type in container_types:
            with self.subTest(container_type=container_type, block_type=block_type):
                source_key = self.course.id.make_usage_key(
                    block_type, f"test_{block_type}"
                )

                result, reason = _migrate_container(
                    context=context,
                    source_key=source_key,
                    container_type=container_type,
                    title=f"Test {block_type.title()}",
                    children=[],
                )

                self.assertIsNone(reason)
                self.assertIsNotNone(result)

                container_version = result.containerversion
                self.assertEqual(container_version.title, f"Test {block_type.title()}")
                # The container is published
                self.assertFalse(authoring_api.contains_unpublished_changes(container_version.container.pk))

    def test_migrate_container_replace_existing_false(self):
        """
        Test _migrate_container returns existing container when replace_existing=False
        """
        source_key = self.course.id.make_usage_key("vertical", "existing_vertical")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Original Title",
            children=[],
        )

        context.existing_source_to_target_keys[source_key] = [first_result.entity]

        second_result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Updated Title",
            children=[],
        )

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertEqual(first_result.version_num, second_result.version_num)

        container_version = second_result.containerversion
        self.assertEqual(container_version.title, "Original Title")

    def test_migrate_container_same_title(self):
        """
        Test _migrate_container for two containers with the same title

        Using preserve_url_slugs=False to create a new Unit with
        a different URL slug based on the container's Title.
        """
        source_key_1 = self.course.id.make_usage_key("vertical", "human_readable_vertical_1")
        source_key_2 = self.course.id.make_usage_key("vertical", "human_readable_vertical_2")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, _ = _migrate_container(
            context=context,
            source_key=source_key_1,
            container_type=lib_api.ContainerType.Unit,
            title="Original Human Readable Title",
            children=[],
        )

        context.existing_source_to_target_keys[source_key_1] = [first_result.entity]

        second_result, _ = _migrate_container(
            context=context,
            source_key=source_key_2,
            container_type=lib_api.ContainerType.Unit,
            title="Original Human Readable Title",
            children=[],
        )

        self.assertNotEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.entity.key, second_result.entity.key)
        # Make sure the current logic from tasts::_find_unique_slug is used
        self.assertEqual(second_result.entity.key, first_result.entity.key + "_1")

        container_version = second_result.containerversion
        self.assertEqual(container_version.title, "Original Human Readable Title")

    def test_migrate_container_replace_existing_true(self):
        """
        Test _migrate_container creates new version when replace_existing=True
        """
        source_key = self.course.id.make_usage_key("vertical", "replaceable_vertical")

        child_component = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "problem"
            ),
            local_key="child_problem",
            created=timezone.now(),
            created_by=self.user.id,
        )
        child_version = authoring_api.create_next_component_version(
            child_component.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Update,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        first_result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Original Title",
            children=[],
        )

        context.existing_source_to_target_keys[source_key] = [first_result.entity]

        second_result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Updated Title",
            children=[child_version.publishable_entity_version],
        )

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.version_num, second_result.version_num)

        container_version = second_result.containerversion
        self.assertEqual(container_version.title, "Updated Title")
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 1)

    def test_migrate_container_with_library_source_key(self):
        """
        Test _migrate_container with library source key
        """
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        source_key = library_key.make_usage_key("vertical", "library_vertical")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Library Vertical",
            children=[],
        )

        self.assertIsNotNone(result)

        container_version = result.containerversion
        self.assertEqual(container_version.title, "Library Vertical")

    def test_migrate_container_empty_children_list(self):
        """
        Test _migrate_container handles empty children list
        """
        source_key = self.course.id.make_usage_key("vertical", "empty_vertical")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Empty Vertical",
            children=[],
        )

        self.assertIsNone(reason)
        self.assertIsNotNone(result)

        container_version = result.containerversion
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 0)

    def test_migrate_container_preserves_child_order(self):
        """
        Test _migrate_container preserves the order of children
        """
        source_key = self.course.id.make_usage_key("vertical", "ordered_vertical")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )
        children = []
        for i in range(3):
            child_component = authoring_api.create_component(
                self.learning_package.id,
                component_type=authoring_api.get_or_create_component_type(
                    "xblock.v1", "problem"
                ),
                local_key=f"child_problem_{i}",
                created=timezone.now(),
                created_by=self.user.id,
            )
            child_version = authoring_api.create_next_component_version(
                child_component.pk,
                content_to_replace={},
                created=timezone.now(),
                created_by=self.user.id,
            )
            children.append(child_version.publishable_entity_version)

        result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Ordered Vertical",
            children=children,
        )

        container_version = result.containerversion
        entity_rows = list(
            container_version.entity_list.entitylistrow_set.order_by("order_num")
        )

        self.assertEqual(len(entity_rows), 3)
        for i, (expected_child, actual_row) in enumerate(zip(children, entity_rows)):
            self.assertEqual(expected_child.entity_id, actual_row.entity_id)

    def test_migrate_container_with_mixed_child_types(self):
        """
        Test _migrate_container with children of different component types
        """
        source_key = self.course.id.make_usage_key("vertical", "mixed_vertical")

        problem_component = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "problem"
            ),
            local_key="mixed_problem",
            created=timezone.now(),
            created_by=self.user.id,
        )
        problem_version = authoring_api.create_next_component_version(
            problem_component.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )

        html_component = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "html"
            ),
            local_key="mixed_html",
            created=timezone.now(),
            created_by=self.user.id,
        )
        html_version = authoring_api.create_next_component_version(
            html_component.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )

        video_component = authoring_api.create_component(
            self.learning_package.id,
            component_type=authoring_api.get_or_create_component_type(
                "xblock.v1", "video"
            ),
            local_key="mixed_video",
            created=timezone.now(),
            created_by=self.user.id,
        )
        video_version = authoring_api.create_next_component_version(
            video_component.pk,
            content_to_replace={},
            created=timezone.now(),
            created_by=self.user.id,
        )

        children = [
            problem_version.publishable_entity_version,
            html_version.publishable_entity_version,
            video_version.publishable_entity_version,
        ]
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, _ = _migrate_container(
            context=context,
            source_key=source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Mixed Content Vertical",
            children=children,
        )

        self.assertIsNotNone(result)

        container_version = result.containerversion
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 3)

        child_entity_ids = set(
            container_version.entity_list.entitylistrow_set.values_list(
                "entity_id", flat=True
            )
        )
        expected_entity_ids = {child.entity_id for child in children}
        self.assertEqual(child_entity_ids, expected_entity_ids)

    def test_migrate_container_generates_correct_target_key(self):
        """
        Test _migrate_container generates correct target key from source key
        """
        course_source_key = self.course.id.make_usage_key("vertical", "test_vertical")
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        course_result, _ = _migrate_container(
            context=context,
            source_key=course_source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Course Vertical",
            children=[],
        )
        context.add_migration(course_source_key, course_result.entity)

        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        library_source_key = library_key.make_usage_key("vertical", "test_vertical")

        library_result, _ = _migrate_container(
            context=context,
            source_key=library_source_key,
            container_type=lib_api.ContainerType.Unit,
            title="Library Vertical",
            children=[],
        )

        self.assertIsNotNone(course_result)
        self.assertIsNotNone(library_result)
        self.assertNotEqual(course_result.entity_id, library_result.entity_id)

    def test_migrate_from_modulestore_success_course(self):
        """
        Test successful migration from course to library
        """
        source = ModulestoreSource.objects.create(key=self.course.id)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

    def test_bulk_migrate_success_courses(self):
        """
        Test successful bulk migration from courses to library
        """
        source_1 = ModulestoreSource.objects.create(key=self.course.id)
        source_2 = ModulestoreSource.objects.create(key=self.course_2.id)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source_1.id, source_2.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id, self.collection2.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source_1.id, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

        migration_2 = ModulestoreMigration.objects.get(
            source=source_2.id, target=self.learning_package
        )
        self.assertEqual(migration_2.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration_2.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

    def test_migrate_from_modulestore_success_legacy_library(self):
        """
        Test successful migration from legacy library to V2 library
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

    def test_bulk_migrate_success_legacy_libraries(self):
        """
        Test successful bulk migration from legacy libraries to V2 library
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)
        source_2 = ModulestoreSource.objects.create(key=self.legacy_library_2.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id, source_2.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id, self.collection2.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

        migration_2 = ModulestoreMigration.objects.get(
            source=source_2, target=self.learning_package
        )
        self.assertEqual(migration_2.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration_2.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)

    def test_bulk_migrate_create_collections(self):
        """
        Test successful bulk migration from legacy libraries to V2 library with create collections
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)
        source_2 = ModulestoreSource.objects.create(key=self.legacy_library_2.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id, source_2.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)

        migration_2 = ModulestoreMigration.objects.get(
            source=source_2, target=self.learning_package
        )
        self.assertEqual(migration_2.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration_2.repeat_handling_strategy, RepeatHandlingStrategy.Skip.value)
        self.assertEqual(migration_2.target_collection.title, self.legacy_library_2.display_name)

    @ddt.data(
        RepeatHandlingStrategy.Skip,
        RepeatHandlingStrategy.Update,
    )
    def test_bulk_migrate_use_previous_collection_on_skip_and_update(self, repeat_handling_strategy):
        """
        Test successful bulk migration from legacy libraries to V2 library using previous collection
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": repeat_handling_strategy.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, repeat_handling_strategy.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)

        # Migrate again and check that the migration uses the previos collection
        previous_collection = migration.target_collection

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": repeat_handling_strategy.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )
        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migrations = ModulestoreMigration.objects.filter(
            source=source, target=self.learning_package
        )

        for migration in migrations:
            self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
            self.assertEqual(migration.repeat_handling_strategy, repeat_handling_strategy.value)
            self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)
            self.assertEqual(migration.target_collection.id, previous_collection.id)

    @ddt.data(
        RepeatHandlingStrategy.Skip,
        RepeatHandlingStrategy.Update,
    )
    def test_bulk_migrate_create_collection_in_different_learning_packages(self, repeat_handling_strategy):
        """
        Test successful bulk migration from legacy libraries to different V2 libraries
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": repeat_handling_strategy.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, repeat_handling_strategy.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)

        # Migrate again in other V2 library, verify that the collections are different
        previous_collection = migration.target_collection

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key_2),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": repeat_handling_strategy.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )
        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, repeat_handling_strategy.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)
        self.assertEqual(migration.target_collection.id, previous_collection.id)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package_2
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, repeat_handling_strategy.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)
        self.assertNotEqual(migration.target_collection.id, previous_collection.id)

    def test_bulk_migrate_create_a_new_collection_on_fork(self):
        """
        Test successful bulk migration from legacy libraries to V2 library using previous collection
        """
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": RepeatHandlingStrategy.Fork.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migration.repeat_handling_strategy, RepeatHandlingStrategy.Fork.value)
        self.assertEqual(migration.target_collection.title, self.legacy_library.display_name)
        previous_collection = migration.target_collection

        # Migrate again and check that it creates a new collection
        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [],
                "create_collections": True,
                "repeat_handling_strategy": RepeatHandlingStrategy.Fork.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )
        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migrations = ModulestoreMigration.objects.filter(
            source=source, target=self.learning_package
        )

        # First migration
        self.assertEqual(migrations[0].composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migrations[0].repeat_handling_strategy, RepeatHandlingStrategy.Fork.value)
        self.assertEqual(migrations[0].target_collection.title, self.legacy_library.display_name)
        self.assertEqual(migrations[0].target_collection.id, previous_collection.id)

        # Second migration
        self.assertEqual(migrations[1].composition_level, CompositionLevel.Unit.value)
        self.assertEqual(migrations[1].repeat_handling_strategy, RepeatHandlingStrategy.Fork.value)
        self.assertEqual(migrations[1].target_collection.title, f"{self.legacy_library.display_name}_1")
        self.assertNotEqual(migrations[1].target_collection.id, previous_collection.id)

    def test_migrate_from_modulestore_library_validation_failure(self):
        """
        Test migration from legacy library fails when modulestore content doesn't exist
        """
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")

        source = ModulestoreSource.objects.create(key=library_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": None,
                "repeat_handling_strategy": RepeatHandlingStrategy.Update.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Section.value,
                "forward_source_to_target": True,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)

        # Should fail at loading step since we don't have real modulestore content
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(
            self._get_task_status_fail_message(status),
            "Failed to load source item 'lib-block-v1:TestOrg+TestLibrary+type@library+block@library' "
            "from ModuleStore: library-v1:TestOrg+TestLibrary+branch@library"
        )

    def test_migrate_from_modulestore_invalid_source_key_type(self):
        """
        Test migration with invalid source key type
        """
        invalid_key = LibraryLocatorV2.from_string("lib:testorg:invalid")
        source = ModulestoreSource.objects.create(key=invalid_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(
            self._get_task_status_fail_message(status),
            f"Not a valid source context key: {invalid_key}. Source key must reference a course or a legacy library."
        )

    def test_bulk_migrate_invalid_source_key_type(self):
        """
        Test bulk migration with invalid source key type
        """
        invalid_key = LibraryLocatorV2.from_string("lib:testorg:invalid")
        source = ModulestoreSource.objects.create(key=invalid_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(
            self._get_task_status_fail_message(status),
            f"Not a valid source context key: {invalid_key}. Source key must reference a course or a legacy library."
        )

    def test_migrate_component_with_fake_block_type(self):
        """
        Test _migrate_component with with_fake_block_type
        """
        source_key = self.course.id.make_usage_key("fake_block", "test_fake_block")
        olx = '<fake_block display_name="Test fake_block"></fake_block>'
        context = _MigrationContext(
            existing_source_to_target_keys={},
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            source_context_key=self.course.id,
            content_by_filename={},
            composition_level=CompositionLevel.Unit,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip,
            preserve_url_slugs=True,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        result, reason = _migrate_component(
            context=context,
            source_key=source_key,
            olx=olx,
            title="test"
        )

        self.assertIsNone(result)
        self.assertEqual(reason, "Invalid block type: fake_block")

    def test_migrate_from_modulestore_nonexistent_modulestore_item(self):
        """
        Test migration when modulestore item doesn't exist
        """
        nonexistent_course_key = CourseKey.from_string(
            "course-v1:NonExistent+Course+Run"
        )
        source = ModulestoreSource.objects.create(key=nonexistent_course_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(
            self._get_task_status_fail_message(status),
            "Failed to load source item 'block-v1:NonExistent+Course+Run+type@course+block@course' "
            "from ModuleStore: course-v1:NonExistent+Course+Run+branch@draft-branch"
        )

    def test_bulk_migrate_nonexistent_modulestore_item(self):
        """
        Test bulk migration when modulestore item doesn't exist
        """
        nonexistent_course_key = CourseKey.from_string(
            "course-v1:NonExistent+Course+Run"
        )
        source = ModulestoreSource.objects.create(key=nonexistent_course_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        self.assertEqual(
            self._get_task_status_fail_message(status),
            "Failed to load source item 'block-v1:NonExistent+Course+Run+type@course+block@course' "
            "from ModuleStore: course-v1:NonExistent+Course+Run+branch@draft-branch"
        )

    def test_migrate_from_modulestore_task_status_progression(self):
        """Test that task status progresses through expected steps"""
        source = ModulestoreSource.objects.create(key=self.course.id)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)

        # Should either succeed or fail, but should have progressed past validation
        self.assertIn(status.state, [UserTaskStatus.SUCCEEDED, UserTaskStatus.FAILED])

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.task_status, status)

    def test_migrate_from_modulestore_multiple_users_no_interference(self):
        """
        Test that migrations by different users don't interfere with each other
        """
        source = ModulestoreSource.objects.create(key=self.course.id)
        other_user = UserFactory()

        task1 = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        task2 = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": other_user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status1 = UserTaskStatus.objects.get(task_id=task1.id)
        status2 = UserTaskStatus.objects.get(task_id=task2.id)

        self.assertEqual(status1.user, self.user)
        self.assertEqual(status2.user, other_user)

        # The first task should not be cancelled since it's from a different user
        self.assertNotEqual(status1.state, UserTaskStatus.CANCELED)

    def test_bulk_migrate_multiple_users_no_interference(self):
        """
        Test that migrations by different users don't interfere with each other
        """
        source = ModulestoreSource.objects.create(key=self.course.id)
        other_user = UserFactory()

        task1 = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        task2 = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": other_user.id,
                "sources_pks": [source.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status1 = UserTaskStatus.objects.get(task_id=task1.id)
        status2 = UserTaskStatus.objects.get(task_id=task2.id)

        self.assertEqual(status1.user, self.user)
        self.assertEqual(status2.user, other_user)

        # The first task should not be cancelled since it's from a different user
        self.assertNotEqual(status1.state, UserTaskStatus.CANCELED)

    @patch("cms.djangoapps.modulestore_migrator.tasks._import_assets")
    def test_migrate_fails_on_import(self, mock_import_assets):
        """
        Test failed migration from legacy library to V2 library
        """
        mock_import_assets.side_effect = Exception("Simulated import error")
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_library_key": str(self.lib_key),
                "target_collection_pk": self.collection.id,
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertTrue(migration.is_failed)

    @patch("cms.djangoapps.modulestore_migrator.tasks._import_assets")
    def test_bulk_migrate_fails_on_import(self, mock_import_assets):
        """
        Test failed bulk migration from legacy libraries to V2 library
        """
        mock_import_assets.side_effect = Exception("Simulated import error")
        source = ModulestoreSource.objects.create(key=self.legacy_library.location.library_key)
        source_2 = ModulestoreSource.objects.create(key=self.legacy_library_2.location.library_key)

        task = bulk_migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "sources_pks": [source.id, source_2.id],
                "target_library_key": str(self.lib_key),
                "target_collection_pks": [self.collection.id, self.collection2.id],
                "repeat_handling_strategy": RepeatHandlingStrategy.Skip.value,
                "preserve_url_slugs": True,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        status = UserTaskStatus.objects.get(task_id=task.id)
        # The task is successful because the entire bulk migration ends successfully.
        # When a legacy library fails to import, it is marked as failed but continues to the next one.
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertTrue(migration.is_failed)

        migration_2 = ModulestoreMigration.objects.get(
            source=source_2, target=self.learning_package
        )
        self.assertTrue(migration_2.is_failed)
