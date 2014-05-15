"""
Unit tests for the container view.
"""

import json

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import compute_publish_state, PublishState
from contentstore.views.helpers import xblock_studio_url
from xmodule.modulestore.django import loc_mapper, modulestore
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
        branch_name = "MITx.999.Robot_Super_Course/branch/draft/block"
        self._test_html_content(
            self.child_vertical,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden" '
                'data-locator="{branch_name}/Child_Vertical">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Child Vertical</a>'
            ).format(branch_name=branch_name)
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
        branch_name = "MITx.999.Robot_Super_Course/branch/draft/block"
        self._test_html_content(
            published_xblock_with_child,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden" '
                'data-locator="{branch_name}/Wrapper">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="/container/{branch_name}/Child_Vertical"\s*'
                r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'
            ).format(branch_name=branch_name)
        )

        # Now make the unit and its children into a draft and validate the container again
        modulestore('draft').convert_to_draft(self.vertical.location)
        modulestore('draft').convert_to_draft(self.child_vertical.location)
        draft_xblock_with_child = modulestore('draft').convert_to_draft(published_xblock_with_child.location)
        self._test_html_content(
            draft_xblock_with_child,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden" '
                'data-locator="{branch_name}/Wrapper">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="/container/{branch_name}/Child_Vertical"\s*'
                r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'
            ).format(branch_name=branch_name)
        )

    def _test_html_content(self, xblock, branch_name, expected_section_tag, expected_breadcrumbs):
        """
        Get the HTML for a container page and verify the section tag is correct
        and the breadcrumbs trail is correct.
        """
        url = xblock_studio_url(xblock, self.course)
        publish_state = compute_publish_state(xblock)
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content
        self.assertIn(expected_section_tag, html)
        # Verify the navigation link at the top of the page is correct.
        self.assertRegexpMatches(html, expected_breadcrumbs)
        # Verify the link that allows users to change publish status.
        expected_message = None
        if publish_state == PublishState.public:
            expected_message = 'you need to edit unit <a href="/unit/{branch_name}/Unit">Unit</a> as a draft.'
        else:
            expected_message = 'your changes will be published with unit <a href="/unit/{branch_name}/Unit">Unit</a>.'
        expected_unit_link = expected_message.format(
            branch_name=branch_name
        )
        self.assertIn(expected_unit_link, html)

    def test_container_preview_html(self):
        """
        Verify that an xblock returns the expected HTML for a container preview
        """
        # First verify that the behavior is correct with a published container
        self._test_preview_html(self.vertical)
        self._test_preview_html(self.child_vertical)

        # Now make the unit and its children into a draft and validate the preview again
        draft_unit = modulestore('draft').convert_to_draft(self.vertical.location)
        draft_container = modulestore('draft').convert_to_draft(self.child_vertical.location)
        self._test_preview_html(draft_unit)
        self._test_preview_html(draft_container)

    def _test_preview_html(self, xblock):
        """
        Verify that the specified xblock has the expected HTML elements for container preview
        """
        locator = loc_mapper().translate_location(self.course.id, xblock.location, published=False)
        publish_state = compute_publish_state(xblock)
        preview_url = '/xblock/{locator}/container_preview'.format(locator=locator)

        resp = self.client.get(preview_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)
        resp_content = json.loads(resp.content)
        html = resp_content['html']

        # Verify that there are no drag handles for public pages
        drag_handle_html = '<span data-tooltip="Drag to reorder" class="drag-handle action"></span>'
        if publish_state == PublishState.public:
            self.assertNotIn(drag_handle_html, html)
        else:
            self.assertIn(drag_handle_html, html)
