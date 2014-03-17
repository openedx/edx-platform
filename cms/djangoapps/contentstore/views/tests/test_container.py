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
        self._test_html_content(
            self.child_vertical,
            expected_section_tag='<section class="wrapper-xblock level-page" data-locator="MITx.999.Robot_Super_Course/branch/draft/block/Child_Vertical"/>',
            expected_breadcrumbs=(
                r'<a href="/unit/MITx.999.Robot_Super_Course/branch/draft/block/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Child Vertical</a>'),
        )

    def test_container_on_container_html(self):
        """
        Create the scenario of an xblock with children (non-vertical) on the container page.
        This should create a container page that is a child of another container page.
        """
        xblock_with_child = ItemFactory.create(parent_location=self.child_vertical.location,
                                               category="wrapper", display_name="Wrapper")
        ItemFactory.create(parent_location=xblock_with_child.location,
                           category="html", display_name="Child HTML")
        self._test_html_content(
            xblock_with_child,
            expected_section_tag='<section class="wrapper-xblock level-page" data-locator="MITx.999.Robot_Super_Course/branch/draft/block/Wrapper"/>',
            expected_breadcrumbs=(
                r'<a href="/unit/MITx.999.Robot_Super_Course/branch/draft/block/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="/container/MITx.999.Robot_Super_Course/branch/draft/block/Child_Vertical"\s*'
                r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'),
        )

    def _test_html_content(self, xblock, expected_section_tag, expected_breadcrumbs):
        """
        Get the HTML for a container page and verify the section tag is correct
        and the breadcrumbs trail is correct.
        """
        url = xblock_studio_url(xblock, self.course)
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content
        self.assertIn(expected_section_tag, html)
        # Verify the navigation link at the top of the page is correct.
        self.assertRegexpMatches(html, expected_breadcrumbs)
        # Verify the link that allows users to change publish status.
        expected_unit_link = 'This content is published with unit <a href="/unit/MITx.999.Robot_Super_Course/branch/draft/block/Unit">Unit</a>.'
        self.assertIn(expected_unit_link, html)
