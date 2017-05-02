from common.test.acceptance.tests.studio.base_studio_test import ContainerBase
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.container import ContainerPage, XBlockWrapper
from common.test.acceptance.pages.studio.utils import add_component
from common.test.acceptance.pages.studio.discussion_component_editor import DiscussionComponentEditor


class DiscussionComponentTest(ContainerBase):
    """
    Feature: CMS.Component Adding
    As a course author, I want to be able to add and edit Discussion component
    """
    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(DiscussionComponentTest, self).setUp(is_staff=is_staff)

    def populate_course_fixture(self, course_fixture):
        """
        Adds a course fixture
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                    )
                )
            )

    def test_view_discussion_component_metadata(self):
        """
        Scenario: Staff user can view discussion component metadata
            Given I am in Studio and I have added a Discussion component
            When I edit Discussion component
            Then I see three settings and their expected values
        """
        component = 'discussion'
        unit = self.go_to_unit_page()
        container_page = ContainerPage(self.browser, None)
        # Add Discussion component
        add_component(container_page, 'discussion', component)
        component = unit.xblocks[1]
        container_page.edit()
        discussion_editor = DiscussionComponentEditor(self.browser, component.locator)
        field_values = discussion_editor.get_edit_discussion_field_values()
        self.assertEqual(
            field_values,
            ['Discussion', 'Week 1', 'Topic-Level Student-Visible Label']
        )

    def test_edit_discussion_component(self):
        """
        Scenario: Staff user can modify display name
            Given I am in Studio and I have added a Discussion component
            When I open Discussion component's edit dialogue
            Then I can modify the display name
            And My display name change is persisted on save
        """
        component = 'discussion'
        unit = self.go_to_unit_page()
        container_page = ContainerPage(self.browser, None)
        # Add Discussion component
        add_component(container_page, 'discussion', component)
        component = unit.xblocks[1]
        container_page.edit()
        discussion_editor = DiscussionComponentEditor(self.browser, component.locator)
        discussion_editor.set_field_val('Display Name', 'Test Name')
        discussion_editor.save()
        component_name = unit.get_xblock_name[0]
        self.assertEqual(component_name, 'Test Name')