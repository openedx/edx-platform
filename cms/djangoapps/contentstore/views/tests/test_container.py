"""
Unit tests for the container view.
"""

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import compute_publish_state, PublishState
from contentstore.views.helpers import xblock_studio_url
from xmodule.modulestore.django import modulestore
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
            expected_location_in_section_tag=self.child_vertical.location,
            expected_breadcrumbs=(
                r'<a href="/unit/{unit_location}"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Child Vertical</a>'
            ).format(unit_location=(unicode(self.vertical.location).replace("+", "\\+")))
        )

    def test_container_on_container_html(self):
        """
        Create the scenario of an xblock with children (non-vertical) on the container page.
        This should create a container page that is a child of another container page.
        """
        published_xblock_with_child = ItemFactory.create(
            parent_location=self.child_vertical.location,
            category="wrapper", display_name="Wrapper"
        )
        ItemFactory.create(
            parent_location=published_xblock_with_child.location,
            category="html", display_name="Child HTML"
        )
        draft_xblock_with_child = modulestore('draft').convert_to_draft(published_xblock_with_child.location)
        expected_breadcrumbs = (
            r'<a href="/unit/{unit_location}"\s*'
            r'class="navigation-link navigation-parent">Unit</a>\s*'
            r'<a href="/container/{child_vertical_location}"\s*'
            r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
            r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'
        ).format(
            unit_location=unicode(self.vertical.location).replace("+", "\\+"),
            child_vertical_location=unicode(self.child_vertical.location).replace("+", "\\+"),
        )
        self._test_html_content(
            published_xblock_with_child,
            expected_location_in_section_tag=published_xblock_with_child.location,
            expected_breadcrumbs=expected_breadcrumbs
        )
        self._test_html_content(
            draft_xblock_with_child,
            expected_location_in_section_tag=draft_xblock_with_child.location,
            expected_breadcrumbs=expected_breadcrumbs
        )

    def _test_html_content(self, xblock, expected_location_in_section_tag, expected_breadcrumbs):
        """
        Get the HTML for a container page and verify the section tag is correct
        and the breadcrumbs trail is correct.
        """
        publish_state = compute_publish_state(xblock)
        url = xblock_studio_url(xblock)
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content
        expected_section_tag = \
            '<section class="wrapper-xblock level-page is-hidden" ' \
            'data-locator="{child_location}" ' \
            'data-course-key="{course_key}">'.format(
                child_location=unicode(expected_location_in_section_tag),
                course_key=unicode(expected_location_in_section_tag.course_key)
            )

        self.assertIn(expected_section_tag, html)
        # Verify the navigation link at the top of the page is correct.
        self.assertRegexpMatches(html, expected_breadcrumbs)
        # Verify the link that allows users to change publish status.
        if publish_state == PublishState.public:
            expected_message = 'you need to edit unit <a href="/unit/{unit_location}">Unit</a> as a draft.'
        else:
            expected_message = 'your changes will be published with unit <a href="/unit/{unit_location}">Unit</a>.'
        expected_unit_link = expected_message.format(
            unit_location=unicode(self.vertical.location)
        )
        self.assertIn(expected_unit_link, html)
