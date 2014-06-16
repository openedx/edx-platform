"""
Unit tests for the unit page.
"""

from contentstore.views.tests.utils import StudioPageTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.x_module import STUDENT_VIEW


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
        self.store = modulestore()

    def test_public_component_preview_html(self):
        """
        Verify that a public xblock's preview returns the expected HTML.
        """
        published_video = self.store.publish(self.video.location, self.user.id)
        self.validate_preview_html(self.video, STUDENT_VIEW, can_add=False)

    def test_draft_component_preview_html(self):
        """
        Verify that a draft xblock's preview returns the expected HTML.
        """
        self.validate_preview_html(self.video, STUDENT_VIEW, can_add=False)

    def test_public_child_container_preview_html(self):
        """
        Verify that a public child container rendering on the unit page (which shows a View arrow
        to the container page) returns the expected HTML.
        """
        child_container = ItemFactory.create(parent_location=self.vertical.location,
                                             category='split_test', display_name='Split Test')
        ItemFactory.create(parent_location=child_container.location,
                           category='html', display_name='grandchild')
        published_child_container = self.store.publish(child_container.location, self.user.id)
        self.validate_preview_html(published_child_container, STUDENT_VIEW, can_add=False)

    def test_draft_child_container_preview_html(self):
        """
        Verify that a draft child container rendering on the unit page (which shows a View arrow
        to the container page) returns the expected HTML.
        """
        child_container = ItemFactory.create(parent_location=self.vertical.location,
                                             category='split_test', display_name='Split Test')
        ItemFactory.create(parent_location=child_container.location,
                           category='html', display_name='grandchild')
        draft_child_container = self.store.get_item(child_container.location)
        self.validate_preview_html(draft_child_container, STUDENT_VIEW, can_add=False)
