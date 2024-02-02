"""
Test the objecttag_export_helpers module
"""
from unittest.mock import patch

from openedx_tagging.core.tagging.models import Tag
from organizations.models import Organization

from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

from .... import api
from ....models import ContentObjectTag
from ..objecttag_export_helpers import TaggedContent, build_object_tree_with_objecttags, iterate_with_level


class TaggedCourseMixin(ModuleStoreTestCase):
    """
    Mixin with a course structure and taxonomies
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    CREATE_USER = False

    def setUp(self):
        super().setUp()
        # Create user
        self.user = UserFactory.create()

        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.taxonomy_1 = api.create_taxonomy(name="Taxonomy 1")
        api.set_taxonomy_orgs(self.taxonomy_1, all_orgs=True)
        Tag.objects.create(
            taxonomy=self.taxonomy_1,
            value="Tag 1.1",
        )
        Tag.objects.create(
            taxonomy=self.taxonomy_1,
            value="Tag 1.2",
        )

        self.taxonomy_2 = api.create_taxonomy(name="Taxonomy 2")
        api.set_taxonomy_orgs(self.taxonomy_2, all_orgs=True)

        Tag.objects.create(
            taxonomy=self.taxonomy_2,
            value="Tag 2.1",
        )
        Tag.objects.create(
            taxonomy=self.taxonomy_2,
            value="Tag 2.2",
        )

        self.patcher = patch("openedx.core.djangoapps.content_tagging.tasks.modulestore", return_value=self.store)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()

        # Create course
        self.course = CourseFactory.create(
            org=self.orgA.short_name,
            number="test_course",
            run="test_run",
            display_name="Test Course",
        )
        course_tags = api.tag_content_object(
            object_key=self.course.id,
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1'],
        )

        self.expected_tagged_xblock = TaggedContent(
            display_name="Test Course",
            block_id="course-v1:orgA+test_course+test_run",
            category="course",
            children=[],
            object_tags={
                self.taxonomy_1.id: list(course_tags),
            },
        )

        # Create XBlocks
        self.sequential = BlockFactory.create(
            parent=self.course,
            category="sequential",
            display_name="test sequential",
        )
        # Tag blocks
        sequential_tags1 = api.tag_content_object(
            object_key=self.sequential.location,
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1', 'Tag 1.2'],
        )
        sequential_tags2 = api.tag_content_object(
            object_key=self.sequential.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        tagged_sequential = TaggedContent(
            display_name="test sequential",
            block_id="block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            category="sequential",
            children=[],
            object_tags={
                self.taxonomy_1.id: list(sequential_tags1),
                self.taxonomy_2.id: list(sequential_tags2),
            },
        )

        assert self.expected_tagged_xblock.children is not None  # type guard
        self.expected_tagged_xblock.children.append(tagged_sequential)

        # Untagged blocks
        sequential2 = BlockFactory.create(
            parent=self.course,
            category="sequential",
            display_name="untagged sequential",
        )
        untagged_sequential = TaggedContent(
            display_name="untagged sequential",
            block_id="block-v1:orgA+test_course+test_run+type@sequential+block@untagged_sequential",
            category="sequential",
            children=[],
            object_tags={},
        )
        assert self.expected_tagged_xblock.children is not None  # type guard
        self.expected_tagged_xblock.children.append(untagged_sequential)
        BlockFactory.create(
            parent=sequential2,
            category="vertical",
            display_name="untagged vertical",
        )
        untagged_vertical = TaggedContent(
            display_name="untagged vertical",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@untagged_vertical",
            category="vertical",
            children=[],
            object_tags={},
        )
        assert untagged_sequential.children is not None  # type guard
        untagged_sequential.children.append(untagged_vertical)
        # /Untagged blocks

        vertical = BlockFactory.create(
            parent=self.sequential,
            category="vertical",
            display_name="test vertical1",
        )
        vertical_tags = api.tag_content_object(
            object_key=vertical.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.2'],
        )
        tagged_vertical = TaggedContent(
            display_name="test vertical1",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1",
            category="vertical",
            children=[],
            object_tags={
                self.taxonomy_2.id: list(vertical_tags),
            },
        )

        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(tagged_vertical)

        vertical2 = BlockFactory.create(
            parent=self.sequential,
            category="vertical",
            display_name="test vertical2",
        )
        untagged_vertical2 = TaggedContent(
            display_name="test vertical2",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical2",
            category="vertical",
            children=[],
            object_tags={},
        )
        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(untagged_vertical2)

        html = BlockFactory.create(
            parent=vertical2,
            category="html",
            display_name="test html",
        )
        html_tags = api.tag_content_object(
            object_key=html.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        tagged_text = TaggedContent(
            display_name="test html",
            block_id="block-v1:orgA+test_course+test_run+type@html+block@test_html",
            category="html",
            children=[],
            object_tags={
                self.taxonomy_2.id: list(html_tags),
            },
        )

        assert untagged_vertical2.children is not None  # type guard
        untagged_vertical2.children.append(tagged_text)

        # Create "deleted" object tags, which will be omitted from the results.
        for object_id in (
            self.course.id,
            self.sequential.location,
            vertical.location,
            html.location,
        ):
            ContentObjectTag.objects.create(
                object_id=str(object_id),
                taxonomy=None,
                tag=None,
                _value="deleted tag",
                _name="deleted taxonomy",
            )

        self.all_object_tags, _ = api.get_all_object_tags(self.course.id)
        self.expected_tagged_content_list = [
            (self.expected_tagged_xblock, 0),
            (tagged_sequential, 1),
            (tagged_vertical, 2),
            (untagged_vertical2, 2),
            (tagged_text, 3),
            (untagged_sequential, 1),
            (untagged_vertical, 2),
        ]


class TestContentTagChildrenExport(TaggedCourseMixin):  # type: ignore[misc]
    """
    Test helper functions for exporting tagged content
    """
    def test_build_object_tree(self) -> None:
        """
        Test if we can export a course
        """
        with self.assertNumQueries(3):
            tagged_xblock = build_object_tree_with_objecttags(self.course.id, self.all_object_tags)

        assert tagged_xblock == self.expected_tagged_xblock

    def test_iterate_with_level(self) -> None:
        """
        Test if we can iterate over the tagged content in the correct order
        """
        tagged_content_list = list(iterate_with_level(self.expected_tagged_xblock))
        assert tagged_content_list == self.expected_tagged_content_list
