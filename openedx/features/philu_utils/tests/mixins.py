"""
Mixins for unit tests
"""
import time

from openedx.core.djangolib.testing.philu_utils import clear_philu_theme, configure_philu_theme
from openedx.features.philu_utils.course import get_course_structure
from xmodule.modulestore.tests.factories import ItemFactory


class PhiluThemeMixin(object):
    """
    Mixin class for PhilU site and site theme
    """

    @classmethod
    def setUpClass(cls):
        super(PhiluThemeMixin, cls).setUpClass()
        configure_philu_theme()

    @classmethod
    def tearDownClass(cls):
        clear_philu_theme()
        super(PhiluThemeMixin, cls).tearDownClass()


class CourseAssessmentMixin(object):
    """
    Base open assessment testcase class, with common methods to create course dynamically.
    """

    def create_course_chapter_with_specific_xblocks(self, store, course, xblock_types):
        """
        Create course chapter with specific xblocks.

        Args:
            store (Modulestore): Module store
            course (Course): Course model object
            xblock_types (list): list of types of xblocks

        Returns:
            None
        """
        for unit in xblock_types:
            self._create_course_children(store, course, 'chapter', unit)

    def _create_course_children(self, store, parent, category, unit):
        """
        Create course children recursively as an input for test cases.
        """
        child_object = ItemFactory.create(
            parent_location=parent.location,
            category=category,
            display_name=u"{} {}".format(category, time.clock()),
            modulestore=store,
            publish_item=True,
        )

        course_structure = get_course_structure()
        if category not in course_structure:
            return

        category = unit if category == 'vertical' else course_structure[category]
        self._create_course_children(store, child_object, category, unit)
