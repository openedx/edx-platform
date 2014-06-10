"""
Unit tests for the unit page.
"""

from contentstore.views.tests.utils import StudioPageTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import ItemFactory


class UnitPageTestCase(StudioPageTestCase):
    """
    Unit tests for the unit page.
    """

    def setUp(self):
        super(UnitPageTestCase, self).setUp()
        self.vertical = ItemFactory.create(parent_location=self.sequential.location,
                                           category='vertical', display_name='Unit')
        self.video = ItemFactory.create(parent_location=self.vertical.location,
                                        category="video", display_name="My Video")

    def test_public_unit_page_html(self):
        """
        Verify that an xblock returns the expected HTML for a public unit page.
        """
        html = self.get_page_html(self.vertical)
        self.validate_html_for_add_buttons(html)

    def test_draft_unit_page_html(self):
        """
        Verify that an xblock returns the expected HTML for a draft unit page.
        """
        draft_unit = modulestore('draft').convert_to_draft(self.vertical.location)
        html = self.get_page_html(draft_unit)
        self.validate_html_for_add_buttons(html)

    def test_public_component_preview_html(self):
        """
        Verify that a public xblock's preview returns the expected HTML.
        """
        self.validate_preview_html(self.video, 'student_view',
                                   can_edit=True, can_reorder=True, can_add=False)

    def test_draft_component_preview_html(self):
        """
        Verify that a draft xblock's preview returns the expected HTML.
        """
        modulestore('draft').convert_to_draft(self.vertical.location)
        draft_video = modulestore('draft').convert_to_draft(self.video.location)
        self.validate_preview_html(draft_video, 'student_view',
                                   can_edit=True, can_reorder=True, can_add=False)

    def test_public_child_container_preview_html(self):
        """
        Verify that a public child container rendering on the unit page (which shows a View arrow
        to the container page) returns the expected HTML.
        """
        child_container = ItemFactory.create(parent_location=self.vertical.location,
                                             category='split_test', display_name='Split Test')
        ItemFactory.create(parent_location=child_container.location,
                           category='html', display_name='grandchild')
        self.validate_preview_html(child_container, 'student_view',
                                   can_reorder=True, can_edit=True, can_add=False)

    def test_draft_child_container_preview_html(self):
        """
        Verify that a draft child container rendering on the unit page (which shows a View arrow
        to the container page) returns the expected HTML.
        """
        child_container = ItemFactory.create(parent_location=self.vertical.location,
                                             category='split_test', display_name='Split Test')
        ItemFactory.create(parent_location=child_container.location,
                           category='html', display_name='grandchild')
        modulestore('draft').convert_to_draft(self.vertical.location)
        draft_child_container = modulestore('draft').get_item(child_container.location)
        self.validate_preview_html(draft_child_container, 'student_view',
                                   can_reorder=True, can_edit=True, can_add=False)
