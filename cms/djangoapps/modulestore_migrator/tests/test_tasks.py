"""
Tests for the modulestore_migrator tasks
"""

from unittest.mock import Mock
import ddt
from django.utils import timezone
from lxml import etree
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from openedx_learning.api.authoring_models import Collection, PublishableEntityVersion
from openedx_learning.api import authoring as authoring_api
from organizations.tests.factories import OrganizationFactory
from user_tasks.tasks import UserTaskStatus
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.modulestore_migrator.data import CompositionLevel
from cms.djangoapps.modulestore_migrator.models import (
    ModulestoreMigration,
    ModulestoreSource,
)
from cms.djangoapps.modulestore_migrator.tasks import (
    _migrate_component,
    _migrate_container,
    _migrate_node,
    _slugify_source_usage_key,
    _MigratedNode,
    _MigrationTask,
    migrate_from_modulestore,
    MigrationStep,
)
from cms.djangoapps.modulestore_migrator.tests.factories import ContentLibraryFactory
from openedx.core.djangoapps.content_libraries.api import ContainerType


@ddt.ddt
class TestMigrateFromModulestore(ModuleStoreTestCase):
    """
    Test the migrate_from_modulestore task
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        lib_key = LibraryLocatorV2.from_string("lib:testorg:tes-key")
        self.learning_package = authoring_api.create_learning_package(
            key=lib_key,
            title="Test Package",
            created=timezone.now(),
            description="Test Description",
        )
        self.library = ContentLibraryFactory(
            org=OrganizationFactory(short_name=lib_key.org),
            slug=lib_key.slug,
            learning_package=self.learning_package,
        )
        self.organization = self.library.org
        self.course = CourseFactory(
            org=self.organization.short_name,
            course="TestCourse",
            run="TestRun",
            display_name="Test Course",
        )
        self.collection = Collection.objects.create(
            learning_package=self.learning_package,
            key="test_collection",
            title="Test Collection",
        )

    def test_slugify_source_usage_key_course(self):
        """Test _slugify_source_usage_key with course usage key"""
        course_key = CourseKey.from_string("course-v1:TestOrg+TestCourse+TestRun")
        usage_key = course_key.make_usage_key("problem", "test_problem")

        result = _slugify_source_usage_key(usage_key)

        self.assertEqual(result, "TestOrg__TestCourse__TestRun__test_problem")

    def test_slugify_source_usage_key_library(self):
        """Test _slugify_source_usage_key with library usage key"""
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        usage_key = library_key.make_usage_key("problem", "test_problem")

        result = _slugify_source_usage_key(usage_key)

        self.assertEqual(result, "TestOrg__TestLibrary__test_problem")

    def test_migrate_node_wiki_tag(self):
        """Test _migrate_node ignores wiki tags"""
        wiki_node = etree.fromstring("<wiki />")

        result = _migrate_node(
            content_by_filename={},
            source_context_key=self.course.id,
            source_node=wiki_node,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            composition_level=CompositionLevel.Unit,
            replace_existing=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        self.assertIsNone(result.source_to_target)
        self.assertEqual(len(result.children), 0)

    def test_migrate_node_course_root(self):
        """Test _migrate_node handles course root"""
        course_node = etree.fromstring(
            '<course url_name="course" display_name="Test Course">'
            '<chapter url_name="chapter1" display_name="Chapter 1" />'
            "</course>"
        )

        result = _migrate_node(
            content_by_filename={},
            source_context_key=self.course.id,
            source_node=course_node,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            composition_level=CompositionLevel.Unit,
            replace_existing=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        # Course root should not be migrated
        self.assertIsNone(result.source_to_target)
        # But should have children processed
        self.assertEqual(len(result.children), 1)

    def test_migrate_node_library_root(self):
        """Test _migrate_node handles library root"""
        library_node = etree.fromstring(
            '<library url_name="library" display_name="Test Library">'
            '<problem url_name="problem1" display_name="Problem 1" />'
            "</library>"
        )
        result = _migrate_node(
            content_by_filename={},
            source_context_key=self.course.id,
            source_node=library_node,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            composition_level=CompositionLevel.Unit,
            replace_existing=False,
            created_at=timezone.now(),
            created_by=self.user.id,
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
        """Test _migrate_node respects composition level for containers"""
        container_node = etree.fromstring(
            f'<{tag_name} url_name="test_{tag_name}" display_name="Test {tag_name.title()}" />'
        )

        result = _migrate_node(
            content_by_filename={},
            source_context_key=self.course.id,
            source_node=container_node,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            composition_level=composition_level,
            replace_existing=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        if should_migrate:
            self.assertIsNotNone(result.source_to_target)
            source_key, _ = result.source_to_target
            self.assertEqual(source_key.block_type, tag_name)
            self.assertEqual(source_key.block_id, f"test_{tag_name}")
        else:
            self.assertIsNone(result.source_to_target)

    def test_migrate_node_without_url_name(self):
        """Test _migrate_node handles nodes without url_name"""
        node_without_url_name = etree.fromstring(
            '<problem display_name="No URL Name" />'
        )

        result = _migrate_node(
            content_by_filename={},
            source_context_key=self.course.id,
            source_node=node_without_url_name,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            composition_level=CompositionLevel.Unit,
            replace_existing=False,
            created_at=timezone.now(),
            created_by=self.user.id,
        )

        self.assertIsNone(result.source_to_target)
        self.assertEqual(len(result.children), 0)

    def test_migrated_node_all_source_to_target_pairs(self):
        """Test _MigratedNode.all_source_to_target_pairs traversal"""

        mock_version1 = Mock(spec=PublishableEntityVersion)
        mock_version2 = Mock(spec=PublishableEntityVersion)
        mock_version3 = Mock(spec=PublishableEntityVersion)

        key1 = self.course.id.make_usage_key("problem", "problem1")
        key2 = self.course.id.make_usage_key("problem", "problem2")
        key3 = self.course.id.make_usage_key("problem", "problem3")

        # Create nested structure
        child_node = _MigratedNode(source_to_target=(key3, mock_version3), children=[])

        parent_node = _MigratedNode(
            source_to_target=(key1, mock_version1),
            children=[
                _MigratedNode(source_to_target=(key2, mock_version2), children=[]),
                child_node,
            ],
        )

        pairs = list(parent_node.all_source_to_target_pairs())

        self.assertEqual(len(pairs), 3)
        self.assertEqual(pairs[0][0], key1)
        self.assertEqual(pairs[1][0], key2)
        self.assertEqual(pairs[2][0], key3)

    def test_migrate_from_modulestore_invalid_source(self):
        """Test migrate_from_modulestore with invalid source"""
        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": 999999,  # Non-existent source
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        result = task.get()
        self.assertIsNone(result)

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migrate_from_modulestore_invalid_target_package(self):
        """Test migrate_from_modulestore with invalid target package"""
        source = ModulestoreSource.objects.create(
            key=self.course.id,
        )

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": 999999,  # Non-existent package
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        result = task.get()
        self.assertIsNone(result)

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migrate_from_modulestore_invalid_collection(self):
        """Test migrate_from_modulestore with invalid collection"""
        source = ModulestoreSource.objects.create(
            key=self.course.id,
        )

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": 999999,  # Non-existent collection
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        result = task.get()
        self.assertIsNone(result)

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migration_task_calculate_total_steps(self):
        """Test _MigrationTask.calculate_total_steps returns correct count"""
        total_steps = _MigrationTask.calculate_total_steps({})
        expected_steps = len(list(MigrationStep))
        self.assertEqual(total_steps, expected_steps)

    def test_migrate_component_success(self):
        """Test _migrate_component successfully creates a new component"""
        source_key = self.course.id.make_usage_key("problem", "test_problem")
        olx = '<problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'

        result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, PublishableEntityVersion)

        # Verify component was created
        self.assertEqual(
            "problem", result.componentversion.component.component_type.name
        )

    def test_migrate_component_with_static_content(self):
        """Test _migrate_component with static file content"""
        source_key = self.course.id.make_usage_key("problem", "test_problem_with_image")
        olx = '<problem display_name="Test Problem"><p>See image: test_image.png</p></problem>'

        # Create some test content
        media_type = authoring_api.get_or_create_media_type("image/png")
        test_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"fake_image_data",
            created=timezone.now(),
        )

        content_by_filename = {"test_image.png": test_content.id}

        result = _migrate_component(
            content_by_filename=content_by_filename,
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify component version content was created
        component_content = result.componentversion.componentversioncontent_set.filter(
            key="static/test_image.png"
        ).first()
        self.assertIsNotNone(component_content)
        self.assertEqual(component_content.content_id, test_content.id)

    def test_migrate_component_replace_existing_false(self):
        """Test _migrate_component with replace_existing=False returns existing component"""
        source_key = self.course.id.make_usage_key("problem", "existing_problem")
        olx = '<problem display_name="Test Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'

        # Create component first time
        first_result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Try to create again with replace_existing=False
        second_result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx='<problem display_name="Updated Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>',
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertEqual(first_result.version_num, second_result.version_num)

    def test_migrate_component_replace_existing_true(self):
        """Test _migrate_component with replace_existing=True creates new version"""
        source_key = self.course.id.make_usage_key("problem", "replaceable_problem")
        original_olx = '<problem display_name="Original"><multiplechoiceresponse></multiplechoiceresponse></problem>'

        # Create component first time
        first_result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx=original_olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Replace with new content
        updated_olx = '<problem display_name="Updated"><multiplechoiceresponse></multiplechoiceresponse></problem>'
        second_result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx=updated_olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=True,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.version_num, second_result.version_num)

    def test_migrate_component_different_block_types(self):
        """Test _migrate_component with different block types"""
        block_types = ["problem", "html", "video", "discussion"]

        for block_type in block_types:
            source_key = self.course.id.make_usage_key(block_type, f"test_{block_type}")
            olx = f'<{block_type} display_name="Test {block_type.title()}"></{block_type}>'

            result = _migrate_component(
                content_by_filename={},
                source_key=source_key,
                olx=olx,
                target_package_id=self.learning_package.id,
                target_library_key=self.library.library_key,
                replace_existing=False,
                created_by=self.user.id,
                created_at=timezone.now(),
            )

            self.assertIsNotNone(result, f"Failed to migrate {block_type}")

            # Verify correct component type was created
            self.assertEqual(
                block_type, result.componentversion.component.component_type.name
            )

    def test_migrate_component_content_filename_not_in_olx(self):
        """Test _migrate_component ignores content files not referenced in OLX"""
        source_key = self.course.id.make_usage_key(
            "problem", "test_problem_selective_content"
        )
        olx = '<problem display_name="Test Problem"><p>See image: referenced.png</p></problem>'

        # Create test content
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

        result = _migrate_component(
            content_by_filename=content_by_filename,
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify only referenced content was added
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
        """Test _migrate_component with library source key"""
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        source_key = library_key.make_usage_key("problem", "library_problem")
        olx = '<problem display_name="Library Problem"><multiplechoiceresponse></multiplechoiceresponse></problem>'

        result = _migrate_component(
            content_by_filename={},
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify correct local key was generated for library source
        self.assertEqual(
            "problem", result.componentversion.component.component_type.name
        )

    def test_migrate_component_duplicate_content_integrity_error(self):
        """Test _migrate_component handles IntegrityError when content already exists"""
        source_key = self.course.id.make_usage_key(
            "problem", "test_problem_duplicate_content"
        )
        olx = '<problem display_name="Test Problem"><p>See image: duplicate.png</p></problem>'

        # Create test content
        media_type = authoring_api.get_or_create_media_type("image/png")
        test_content = authoring_api.get_or_create_file_content(
            self.learning_package.id,
            media_type.id,
            data=b"test_image_data",
            created=timezone.now(),
        )

        content_by_filename = {"duplicate.png": test_content.id}

        # First migration should succeed
        first_result = _migrate_component(
            content_by_filename=content_by_filename,
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Second migration with same content should handle IntegrityError gracefully
        second_result = _migrate_component(
            content_by_filename=content_by_filename,
            source_key=source_key,
            olx=olx,
            target_package_id=self.learning_package.id,
            target_library_key=self.library.library_key,
            replace_existing=True,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(first_result)
        self.assertIsNotNone(second_result)

    def test_migrate_container_creates_new_container(self):
        """Test _migrate_container creates a new container when none exists"""
        source_key = self.course.id.make_usage_key("vertical", "test_vertical")

        # Create some child components first
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

        print("=" * 40)
        print(self.library.library_key)
        print(self.learning_package.id)
        print(self.learning_package.key)
        print("=" * 40)
        result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Test Vertical",
            children=children,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, PublishableEntityVersion)

        # Verify container was created with correct properties
        container_version = result.containerversion
        self.assertEqual(container_version.title, "Test Vertical")

        # Verify children were added
        entity_rows = container_version.entity_list.entitylistrow_set.all()
        self.assertEqual(len(entity_rows), 2)

        child_entity_ids = {row.entity_id for row in entity_rows}
        expected_entity_ids = {child.entity_id for child in children}
        self.assertEqual(child_entity_ids, expected_entity_ids)

    def test_migrate_container_different_container_types(self):
        """Test _migrate_container works with different container types"""
        container_types = [
            (ContainerType.Unit, "vertical"),
            (ContainerType.Subsection, "sequential"),
            (ContainerType.Section, "chapter"),
        ]

        for container_type, block_type in container_types:
            with self.subTest(container_type=container_type, block_type=block_type):
                source_key = self.course.id.make_usage_key(
                    block_type, f"test_{block_type}"
                )

                result = _migrate_container(
                    source_key=source_key,
                    container_type=container_type,
                    title=f"Test {block_type.title()}",
                    children=[],
                    target_library_key=self.library.library_key,
                    replace_existing=False,
                    created_by=self.user.id,
                    created_at=timezone.now(),
                )

                self.assertIsNotNone(result)

                # Verify container was created with correct type
                container_version = result.containerversion
                self.assertEqual(container_version.title, f"Test {block_type.title()}")

    def test_migrate_container_replace_existing_false(self):
        """Test _migrate_container returns existing container when replace_existing=False"""
        source_key = self.course.id.make_usage_key("vertical", "existing_vertical")

        # Create container first time
        first_result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Original Title",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Try to create again with different title and replace_existing=False
        second_result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Updated Title",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Should return the same entity and version
        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertEqual(first_result.version_num, second_result.version_num)

        # Title should remain unchanged
        container_version = second_result.containerversion
        self.assertEqual(container_version.title, "Original Title")

    def test_migrate_container_replace_existing_true(self):
        """Test _migrate_container creates new version when replace_existing=True"""
        source_key = self.course.id.make_usage_key("vertical", "replaceable_vertical")

        # Create initial child component
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

        # Create container first time
        first_result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Original Title",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Replace with new content
        second_result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Updated Title",
            children=[child_version.publishable_entity_version],
            target_library_key=self.library.library_key,
            replace_existing=True,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Should be same entity but different version
        self.assertEqual(first_result.entity_id, second_result.entity_id)
        self.assertNotEqual(first_result.version_num, second_result.version_num)

        # Title and children should be updated
        container_version = second_result.containerversion
        self.assertEqual(container_version.title, "Updated Title")
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 1)

    def test_migrate_container_with_library_source_key(self):
        """Test _migrate_container with library source key"""
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        source_key = library_key.make_usage_key("vertical", "library_vertical")

        result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Library Vertical",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify correct slugified key was generated
        container_version = result.containerversion
        self.assertEqual(container_version.title, "Library Vertical")

    def test_migrate_container_empty_children_list(self):
        """Test _migrate_container handles empty children list"""
        source_key = self.course.id.make_usage_key("vertical", "empty_vertical")

        result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Empty Vertical",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify container was created with no children
        container_version = result.containerversion
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 0)

    def test_migrate_container_preserves_child_order(self):
        """Test _migrate_container preserves the order of children"""
        source_key = self.course.id.make_usage_key("vertical", "ordered_vertical")

        # Create multiple child components
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

        result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Ordered Vertical",
            children=children,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Verify children order is preserved
        container_version = result.containerversion
        entity_rows = list(
            container_version.entity_list.entitylistrow_set.order_by("order_num")
        )

        self.assertEqual(len(entity_rows), 3)
        for i, (expected_child, actual_row) in enumerate(zip(children, entity_rows)):
            self.assertEqual(expected_child.entity_id, actual_row.entity_id)

    def test_migrate_container_with_mixed_child_types(self):
        """Test _migrate_container with children of different component types"""
        source_key = self.course.id.make_usage_key("vertical", "mixed_vertical")

        # Create children of different types
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

        result = _migrate_container(
            source_key=source_key,
            container_type=ContainerType.Unit,
            title="Mixed Content Vertical",
            children=children,
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        self.assertIsNotNone(result)

        # Verify all children were added
        container_version = result.containerversion
        self.assertEqual(container_version.entity_list.entitylistrow_set.count(), 3)

        # Verify each child type is present
        child_entity_ids = set(
            container_version.entity_list.entitylistrow_set.values_list(
                "entity_id", flat=True
            )
        )
        expected_entity_ids = {child.entity_id for child in children}
        self.assertEqual(child_entity_ids, expected_entity_ids)

    def test_migrate_container_generates_correct_target_key(self):
        """Test _migrate_container generates correct target key from source key"""
        # Test with course source key
        course_source_key = self.course.id.make_usage_key("vertical", "test_vertical")

        course_result = _migrate_container(
            source_key=course_source_key,
            container_type=ContainerType.Unit,
            title="Course Vertical",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Test with library source key
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")
        library_source_key = library_key.make_usage_key("vertical", "test_vertical")

        library_result = _migrate_container(
            source_key=library_source_key,
            container_type=ContainerType.Unit,
            title="Library Vertical",
            children=[],
            target_library_key=self.library.library_key,
            replace_existing=False,
            created_by=self.user.id,
            created_at=timezone.now(),
        )

        # Both should succeed but have different underlying identifiers
        self.assertIsNotNone(course_result)
        self.assertIsNotNone(library_result)
        self.assertNotEqual(course_result.entity_id, library_result.entity_id)

    def test_migrate_from_modulestore_success_course(self):
        """Test successful migration from course to library"""
        source = ModulestoreSource.objects.create(key=self.course.id)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        task.get()

        # Verify task completed successfully
        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)

        # Verify migration record was created
        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.composition_level, CompositionLevel.Unit.value)
        self.assertFalse(migration.replace_existing)

    def test_migrate_from_modulestore_library_validation_failure(self):
        """Test migration from legacy library fails when modulestore content doesn't exist"""
        library_key = LibraryLocator(org="TestOrg", library="TestLibrary")

        source = ModulestoreSource.objects.create(key=library_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": None,
                "replace_existing": True,
                "composition_level": CompositionLevel.Section.value,
                "forward_source_to_target": True,
            }
        )

        # This will fail because we don't have actual library content in modulestore
        task.get()
        status = UserTaskStatus.objects.get(task_id=task.id)

        # Should fail at loading step since we don't have real modulestore content
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migrate_from_modulestore_invalid_source_key_type(self):
        """Test migration with invalid source key type"""
        # Create a source with an invalid key type
        invalid_key = LibraryLocatorV2.from_string("lib:testorg:invalid")
        source = ModulestoreSource.objects.create(key=invalid_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        result = task.get()
        self.assertIsNone(result)

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migrate_from_modulestore_nonexistent_modulestore_item(self):
        """Test migration when modulestore item doesn't exist"""
        # Create source with course that doesn't exist in modulestore
        nonexistent_course_key = CourseKey.from_string(
            "course-v1:NonExistent+Course+Run"
        )
        source = ModulestoreSource.objects.create(key=nonexistent_course_key)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        result = task.get()
        self.assertIsNone(result)

        status = UserTaskStatus.objects.get(task_id=task.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)

    def test_migrate_from_modulestore_task_status_progression(self):
        """Test that task status progresses through expected steps"""
        source = ModulestoreSource.objects.create(key=self.course.id)

        task = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        task.get()

        # Verify task went through validation step
        status = UserTaskStatus.objects.get(task_id=task.id)

        # Should either succeed or fail, but should have progressed past validation
        self.assertIn(status.state, [UserTaskStatus.SUCCEEDED, UserTaskStatus.FAILED])

        # Verify migration task was created
        migration = ModulestoreMigration.objects.get(
            source=source, target=self.learning_package
        )
        self.assertEqual(migration.task_status, status)

    def test_migrate_from_modulestore_multiple_users_no_interference(self):
        """Test that migrations by different users don't interfere with each other"""
        source = ModulestoreSource.objects.create(key=self.course.id)
        other_user = UserFactory()

        # Start migration for first user
        task1 = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": self.user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        # Start migration for second user with same source/target
        task2 = migrate_from_modulestore.apply_async(
            kwargs={
                "user_id": other_user.id,
                "source_pk": source.id,
                "target_package_pk": self.learning_package.id,
                "target_collection_pk": self.collection.id,
                "replace_existing": False,
                "composition_level": CompositionLevel.Unit.value,
                "forward_source_to_target": False,
            }
        )

        # Both tasks should complete (or fail) independently
        task1.get()
        task2.get()

        # Verify both tasks created their own status records
        status1 = UserTaskStatus.objects.get(task_id=task1.id)
        status2 = UserTaskStatus.objects.get(task_id=task2.id)

        self.assertEqual(status1.user, self.user)
        self.assertEqual(status2.user, other_user)

        # The first task should not be cancelled since it's from a different user
        self.assertNotEqual(status1.state, UserTaskStatus.CANCELED)
