"""
Unit tests for the container view.
"""

from contentstore.tests.utils import CourseTestCase
from contentstore.views.helpers import xblock_studio_url
from xmodule.modulestore.tests.factories import ItemFactory


class ContainerViewTestCase(CourseTestCase):
    """
    Unit tests for the container view.
    """

    def setUp(self):
        super(ContainerViewTestCase, self).setUp()
        self.chapter = ItemFactory.create(parent_location=self.course.location,
                                          category='chapter', display_name="Week 1")
        self.sequential = ItemFactory.create(parent_location=self.chapter.location,
                                             category='sequential', display_name="Lesson 1")
        self.vertical = ItemFactory.create(parent_location=self.sequential.location,
                                           category='vertical', display_name='Unit')
        self.child_vertical = ItemFactory.create(parent_location=self.vertical.location,
                                                 category='vertical', display_name='Child Vertical')
        self.video = ItemFactory.create(parent_location=self.child_vertical.location,
                                        category="video", display_name="My Video")

    def test_container_html(self):
        url = xblock_studio_url(self.child_vertical)
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content
        self.assertIn('<section class="wrapper-xblock level-page" data-locator="MITx.999.Robot_Super_Course/branch/published/block/Child_Vertical"/>', html)
