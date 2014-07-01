"""
Unit tests for helpers.py.
"""

from contentstore.tests.utils import CourseTestCase
from contentstore.views.helpers import xblock_studio_url
from xmodule.modulestore.tests.factories import ItemFactory


class HelpersTestCase(CourseTestCase):
    """
    Unit tests for helpers.py.
    """
    def test_xblock_studio_url(self):

        # Verify course URL
        self.assertEqual(xblock_studio_url(self.course),
                         u'/course/MITx/999/Robot_Super_Course')

        # Verify chapter URL
        chapter = ItemFactory.create(parent_location=self.course.location, category='chapter',
                                     display_name="Week 1")
        self.assertIsNone(xblock_studio_url(chapter))

        # Verify lesson URL
        sequential = ItemFactory.create(parent_location=chapter.location, category='sequential',
                                        display_name="Lesson 1")
        self.assertIsNone(xblock_studio_url(sequential))

        # Verify vertical URL
        vertical = ItemFactory.create(parent_location=sequential.location, category='vertical',
                                      display_name='Unit')
        self.assertEqual(xblock_studio_url(vertical),
                         u'/unit/i4x://MITx/999/vertical/Unit')

        # Verify child vertical URL
        child_vertical = ItemFactory.create(parent_location=vertical.location, category='vertical',
                                            display_name='Child Vertical')
        self.assertEqual(xblock_studio_url(child_vertical),
                         u'/container/i4x://MITx/999/vertical/Child_Vertical')

        # Verify video URL
        video = ItemFactory.create(parent_location=child_vertical.location, category="video",
                                   display_name="My Video")
        self.assertIsNone(xblock_studio_url(video))
