"""
This module has tests for utils.py
"""
# pylint: disable=no-member

import ddt

from django.test.utils import override_settings

from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_metadata.utils import get_course_leaf_nodes


@ddt.ddt
class UtilsTests(ModuleStoreTestCase):
    """ Test suite to test operation in utils"""

    def setUp(self):
        super(UtilsTests, self).setUp()

        self.course = CourseFactory.create()
        self.test_data = '<html>Test data</html>'

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            display_name="Overview",
        )
        self.sub_section = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name=u"test subsection",
        )
        self.sub_section2 = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name=u"test subsection 2",
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test vertical",
        )
        self.vertical2 = ItemFactory.create(
            parent_location=self.sub_section2.location,
            category="vertical",
            metadata={'graded': True, 'format': 'FinalExam'},
            display_name=u"test vertical 2",
        )
        self.content_child1 = ItemFactory.create(
            category="html",
            parent_location=self.vertical.location,
            data=self.test_data,
            display_name="Html component"
        )
        self.content_child2 = ItemFactory.create(
            category="video",
            parent_location=self.vertical.location,
            data=self.test_data,
            display_name="Video component"
        )
        self.content_child3 = ItemFactory.create(
            category="group-project",
            parent_location=self.vertical.location,
            data=self.test_data,
            display_name="group project component"
        )
        self.content_child4 = ItemFactory.create(
            category="html",
            parent_location=self.vertical2.location,
            data=self.test_data,
            display_name="Html component 2"
        )
        self.user = UserFactory()

    @override_settings(PROGRESS_DETACHED_CATEGORIES=[])
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_get_course_leaf_nodes(self, module_store_type):
        """
        Tests get_course_leaf_nodes works as expected
        """
        with modulestore().default_store(module_store_type):
            nodes = get_course_leaf_nodes(self.course.id)
            self.assertEqual(len(nodes), 4)

    @override_settings(PROGRESS_DETACHED_CATEGORIES=["group-project"])
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_get_course_leaf_nodes_with_detached_categories(self, module_store_type):
        """
        Tests get_course_leaf_nodes with detached categories
        """
        with modulestore().default_store(module_store_type):
            nodes = get_course_leaf_nodes(self.course.id)
            # group-project project node should not be counted
            self.assertEqual(len(nodes), 3)

    @override_settings(PROGRESS_DETACHED_CATEGORIES=[])
    def test_get_course_leaf_nodes_with_orphan_nodes(self):
        """
        Tests get_course_leaf_nodes if some nodes are orphan
        """
        with modulestore().default_store(ModuleStoreEnum.Type.mongo):
            with modulestore().branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                # delete sub_section2 to make vertical2 orphan
                store = modulestore()
                store.delete_item(self.sub_section2.location, self.user.id)
                nodes = get_course_leaf_nodes(self.course.id)
                self.assertEqual(len(nodes), 3)
