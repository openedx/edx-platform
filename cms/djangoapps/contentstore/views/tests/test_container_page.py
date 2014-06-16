"""
Unit tests for the container page.
"""

import re
from contentstore.views.tests.utils import StudioPageTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import ItemFactory


class ContainerPageTestCase(StudioPageTestCase):
    """
    Unit tests for the container page.
    """

    container_view = 'container_preview'
    reorderable_child_view = 'reorderable_container_child_preview'

    def setUp(self):
        super(ContainerPageTestCase, self).setUp()
        self.vertical = ItemFactory.create(parent_location=self.sequential.location,
                                           category='vertical', display_name='Unit')
        self.html = ItemFactory.create(parent_location=self.vertical.location,
                                        category="html", display_name="HTML")
        self.child_container = ItemFactory.create(parent_location=self.vertical.location,
                                                  category='split_test', display_name='Split Test')
        self.child_vertical = ItemFactory.create(parent_location=self.child_container.location,
                                                 category='vertical', display_name='Child Vertical')
        self.video = ItemFactory.create(parent_location=self.child_vertical.location,
                                        category="video", display_name="My Video")

    def test_container_html(self):
        self._test_html_content(
            self.child_container,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                'data-locator="{0}" data-course-key="{0.course_key}">'.format(self.child_container.location)
            ),
            expected_breadcrumbs=(
                r'<a href="/course/{course}" class="navigation-link navigation-parent">\s*Week 1\s*</a>\s*'
                r'<span class="navigation-parent">\s*Lesson 1\s*</span>\s*'
                r'<a href="/container/{unit}" class="navigation-link navigation-parent">\s*Unit\s*</a>'
            ).format(
                course=re.escape(unicode(self.course.id)),
                unit=re.escape(unicode(self.vertical.location)),
            ),
        )

    def test_container_on_container_html(self):
        """
        Create the scenario of an xblock with children (non-vertical) on the container page.
        This should create a container page that is a child of another container page.
        """
        published_container = ItemFactory.create(
            parent_location=self.child_container.location,
            category="wrapper", display_name="Wrapper"
        )
        ItemFactory.create(
            parent_location=published_container.location,
            category="html", display_name="Child HTML"
        )

        def test_container_html(xblock):
            self._test_html_content(
                xblock,
                expected_section_tag=(
                    '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                    'data-locator="{0}" data-course-key="{0.course_key}">'.format(published_container.location)
                ),
                expected_breadcrumbs=(
                    r'<a href="/course/{course}" class="navigation-link navigation-parent">\s*Week 1\s*</a>\s*'
                    r'<span class="navigation-parent">\s*Lesson 1\s*</span>\s*'
                    r'<a href="/container/{unit}" class="navigation-link navigation-parent">\s*Unit\s*</a>\s*'
                    r'<a href="/container/{split_test}" class="navigation-link navigation-parent">\s*Split Test\s*</a>'
                ).format(
                    course=re.escape(unicode(self.course.id)),
                    unit=re.escape(unicode(self.vertical.location)),
                    split_test=re.escape(unicode(self.child_container.location))
                ),
            )

        # Test the published version of the container
        test_container_html(published_container)

        # Now make the unit and its children into a draft and validate the container again
        modulestore('draft').convert_to_draft(self.vertical.location)
        modulestore('draft').convert_to_draft(self.child_vertical.location)
        draft_container = modulestore('draft').convert_to_draft(published_container.location)
        test_container_html(draft_container)

    def _test_html_content(self, xblock, expected_section_tag, expected_breadcrumbs):
        """
        Get the HTML for a container page and verify the section tag is correct
        and the breadcrumbs trail is correct.
        """
        html = self.get_page_html(xblock)
        self.assertIn(expected_section_tag, html)
        self.assertRegexpMatches(html, expected_breadcrumbs)

    def test_public_container_preview_html(self):
        """
        Verify that a public xblock's container preview returns the expected HTML.
        """
        self.validate_preview_html(self.vertical, self.container_view)
        self.validate_preview_html(self.child_container, self.container_view)
        self.validate_preview_html(self.child_vertical, self.reorderable_child_view)

    def test_draft_container_preview_html(self):
        """
        Verify that a draft xblock's container preview returns the expected HTML.
        """
        # TODO: We should delete some of these test cases when doing publishing story.
        draft_unit = modulestore('draft').convert_to_draft(self.vertical.location)
        draft_child_container = modulestore('draft').convert_to_draft(self.child_container.location)
        draft_child_vertical = modulestore('draft').convert_to_draft(self.child_vertical.location)
        self.validate_preview_html(draft_unit, self.container_view)
        self.validate_preview_html(draft_child_container, self.container_view)
        self.validate_preview_html(draft_child_vertical, self.reorderable_child_view)

    def test_public_child_container_preview_html(self):
        """
        Verify that a public container rendered as a child of the container page returns the expected HTML.
        """
        empty_child_container = ItemFactory.create(parent_location=self.vertical.location,
                                                   category='split_test', display_name='Split Test')
        self.validate_preview_html(empty_child_container, self.reorderable_child_view, can_add=False)

    def test_draft_child_container_preview_html(self):
        """
        Verify that a draft container rendered as a child of the container page returns the expected HTML.
        """
        # TODO: We should delete some of these test cases when doing publishing story.
        empty_child_container = ItemFactory.create(parent_location=self.vertical.location,
                                                   category='split_test', display_name='Split Test')
        modulestore('draft').convert_to_draft(self.vertical.location)
        draft_empty_child_container = modulestore('draft').convert_to_draft(empty_child_container.location)
        self.validate_preview_html(draft_empty_child_container, self.reorderable_child_view, can_add=False)
