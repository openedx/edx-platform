"""
Tests for the LMS/lib utils
"""


from lms.lib import utils
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class LmsUtilsTest(ModuleStoreTestCase):
    """
    Tests for the LMS utility functions
    """

    def setUp(self):
        """
        Setup a dummy course content.
        """
        super(LmsUtilsTest, self).setUp()

        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.html_module_1 = ItemFactory.create(category="html", parent_location=self.vertical.location)
            self.vertical_with_container = ItemFactory.create(
                category="vertical", parent_location=self.sequential.location
            )
            self.child_container = ItemFactory.create(
                category="split_test", parent_location=self.vertical_with_container.location)
            self.child_vertical = ItemFactory.create(category="vertical", parent_location=self.child_container.location)
            self.child_html_module = ItemFactory.create(category="html", parent_location=self.child_vertical.location)

            # Read again so that children lists are accurate
            self.course = self.store.get_item(self.course.location)
            self.chapter = self.store.get_item(self.chapter.location)
            self.sequential = self.store.get_item(self.sequential.location)
            self.vertical = self.store.get_item(self.vertical.location)

            self.vertical_with_container = self.store.get_item(self.vertical_with_container.location)
            self.child_container = self.store.get_item(self.child_container.location)
            self.child_vertical = self.store.get_item(self.child_vertical.location)
            self.child_html_module = self.store.get_item(self.child_html_module.location)

    def test_get_parent_unit(self):
        """
        Tests `get_parent_unit` method for the successful result.
        """
        parent = utils.get_parent_unit(self.html_module_1)
        self.assertEqual(parent.location, self.vertical.location)

        parent = utils.get_parent_unit(self.child_html_module)
        self.assertEqual(parent.location, self.vertical_with_container.location)

        self.assertIsNone(utils.get_parent_unit(None))
        self.assertIsNone(utils.get_parent_unit(self.vertical))
        self.assertIsNone(utils.get_parent_unit(self.course))
        self.assertIsNone(utils.get_parent_unit(self.chapter))
        self.assertIsNone(utils.get_parent_unit(self.sequential))

    def test_is_unit(self):
        """
        Tests `is_unit` method for the successful result.
        """
        self.assertFalse(utils.is_unit(self.html_module_1))
        self.assertFalse(utils.is_unit(self.child_vertical))
        self.assertTrue(utils.is_unit(self.vertical))
