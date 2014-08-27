"""
Unit tests for the container page.
"""

import re
import datetime
from pytz import UTC
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
        self.vertical = self._create_item(self.sequential.location, 'vertical', 'Unit')
        self.html = self._create_item(self.vertical.location, "html", "HTML")
        self.child_container = self._create_item(self.vertical.location, 'split_test', 'Split Test')
        self.child_vertical = self._create_item(self.child_container.location, 'vertical', 'Child Vertical')
        self.video = self._create_item(self.child_vertical.location, "video", "My Video")
        self.store = modulestore()

        past = datetime.datetime(1970, 1, 1, tzinfo=UTC)
        future = datetime.datetime.now(UTC) + datetime.timedelta(days=1)
        self.released_private_vertical = self._create_item(
            parent_location=self.sequential.location, category='vertical', display_name='Released Private Unit',
            start=past)
        self.unreleased_private_vertical = self._create_item(
            parent_location=self.sequential.location, category='vertical', display_name='Unreleased Private Unit',
            start=future)
        self.released_public_vertical = self._create_item(
            parent_location=self.sequential.location, category='vertical', display_name='Released Public Unit',
            start=past)
        self.unreleased_public_vertical = self._create_item(
            parent_location=self.sequential.location, category='vertical', display_name='Unreleased Public Unit',
            start=future)
        self.store.publish(self.unreleased_public_vertical.location, self.user.id)
        self.store.publish(self.released_public_vertical.location, self.user.id)

    def test_container_html(self):
        self._test_html_content(
            self.child_container,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                'data-locator="{0}" data-course-key="{0.course_key}">'.format(self.child_container.location)
            ),
            expected_breadcrumbs=(
                r'<a href="/course/{course}{section_parameters}" class="{classes}">\s*Week 1\s*</a>\s*'
                r'<a href="/course/{course}{subsection_parameters}" class="{classes}">\s*Lesson 1\s*</a>\s*'
                r'<a href="/container/{unit}" class="{classes}">\s*Unit\s*</a>'
            ).format(
                course=re.escape(unicode(self.course.id)),
                unit=re.escape(unicode(self.vertical.location)),
                classes='navigation-item navigation-link navigation-parent',
                section_parameters=re.escape(u'?show=i4x%3A//MITx/999/chapter/Week_1'),
                subsection_parameters=re.escape(u'?show=i4x%3A//MITx/999/sequential/Lesson_1'),
            ),
        )

    def test_container_on_container_html(self):
        """
        Create the scenario of an xblock with children (non-vertical) on the container page.
        This should create a container page that is a child of another container page.
        """
        draft_container = self._create_item(self.child_container.location, "wrapper", "Wrapper")
        self._create_item(draft_container.location, "html", "Child HTML")

        def test_container_html(xblock):
            self._test_html_content(
                xblock,
                expected_section_tag=(
                    '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                    'data-locator="{0}" data-course-key="{0.course_key}">'.format(draft_container.location)
                ),
                expected_breadcrumbs=(
                    r'<a href="/course/{course}{section_parameters}" class="{classes}">\s*Week 1\s*</a>\s*'
                    r'<a href="/course/{course}{subsection_parameters}" class="{classes}">\s*Lesson 1\s*</a>\s*'
                    r'<a href="/container/{unit}" class="{classes}">\s*Unit\s*</a>\s*'
                    r'<a href="/container/{split_test}" class="{classes}">\s*Split Test\s*</a>'
                ).format(
                    course=re.escape(unicode(self.course.id)),
                    unit=re.escape(unicode(self.vertical.location)),
                    split_test=re.escape(unicode(self.child_container.location)),
                    classes='navigation-item navigation-link navigation-parent',
                    section_parameters=re.escape(u'?show=i4x%3A//MITx/999/chapter/Week_1'),
                    subsection_parameters=re.escape(u'?show=i4x%3A//MITx/999/sequential/Lesson_1'),
                ),
            )

        # Test the draft version of the container
        test_container_html(draft_container)

        # Now publish the unit and validate again
        self.store.publish(self.vertical.location, self.user.id)
        draft_container = self.store.get_item(draft_container.location)
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
        published_unit = self.store.publish(self.vertical.location, self.user.id)
        published_child_container = self.store.get_item(self.child_container.location)
        published_child_vertical = self.store.get_item(self.child_vertical.location)
        self.validate_preview_html(published_unit, self.container_view)
        self.validate_preview_html(published_child_container, self.container_view)
        self.validate_preview_html(published_child_vertical, self.reorderable_child_view)

    def test_draft_container_preview_html(self):
        """
        Verify that a draft xblock's container preview returns the expected HTML.
        """
        self.validate_preview_html(self.vertical, self.container_view)
        self.validate_preview_html(self.child_container, self.container_view)
        self.validate_preview_html(self.child_vertical, self.reorderable_child_view)

    def _create_item(self, parent_location, category, display_name, **kwargs):
        """
        creates an item in the module store, without publishing it.
        """
        return ItemFactory.create(
            parent_location=parent_location,
            category=category,
            display_name=display_name,
            publish_item=False,
            user_id=self.user.id,
            **kwargs
        )

    def test_public_child_container_preview_html(self):
        """
        Verify that a public container rendered as a child of the container page returns the expected HTML.
        """
        empty_child_container = self._create_item(self.vertical.location, 'split_test', 'Split Test')
        published_empty_child_container = self.store.publish(empty_child_container.location, self.user.id)
        self.validate_preview_html(published_empty_child_container, self.reorderable_child_view, can_add=False)

    def test_draft_child_container_preview_html(self):
        """
        Verify that a draft container rendered as a child of the container page returns the expected HTML.
        """
        empty_child_container = self._create_item(self.vertical.location, 'split_test', 'Split Test')
        self.validate_preview_html(empty_child_container, self.reorderable_child_view, can_add=False)
