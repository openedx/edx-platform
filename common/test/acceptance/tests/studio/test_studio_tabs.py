"""
Acceptance tests for Studio related to the Pages.
"""
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.edit_tabs import PagesPage


class PagesTest(StudioCourseTest):
    """
    Test that Pages functionality is working properly on studio side
    """

    def setUp(self, is_staff=True):  # pylint: disable=arguments-differ
        """
        Install a course with no content using a fixture.
        """
        super(PagesTest, self).setUp(is_staff)
        self.pages_page = PagesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.pages_page.visit()

    def test_user_can_add_static_tab(self):
        """
        Scenario: Users can add static pages
            Given I have opened the pages page in a new course
                Then I should not see any static pages
            When I add a new static page
                Then I should see a static page named "Empty"
        """
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page for a newly created course'
        )
        self.pages_page.add_static_page()
        self.assertTrue(
            self.pages_page.is_static_page_present(),
            'Static tab should be present on the page'
        )

    def test_user_can_delete_static_tab(self):
        """
        Scenario: Users can delete static pages
            Given I have created a static page
            When I "delete" the static page
                Then I am shown a prompt
            When I confirm the prompt
                Then I should not see any static pages
        """
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page for a newly created course'
        )
        self.pages_page.add_static_page()
        self.pages_page.delete_static_tab()
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page after the deletion'
        )

    def test_user_can_edit_static_tab(self):
        """
        Scenario: Users can edit static pages
            Given I have created a static page
            When I "edit" the static page
            And I change the name to "New"
                Then I should see static page named "New"
        """
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page for a newly created course'
        )
        self.pages_page.add_static_page()
        self.assertNotEqual(self.pages_page.static_tab_titles[0], "New")
        self.pages_page.click_edit_static_page()
        self.pages_page.open_settings_tab()
        self.pages_page.set_field_val("Display Name", "New")
        self.pages_page.save()
        self.assertEqual(self.pages_page.static_tab_titles[0], "New", "The title of the tab is not updated")

    def test_user_can_reorder_static_tabs(self):
        """
        Scenario: Users can reorder static pages
            Given I have created two different static pages
            When I drag the first static page to the last
                Then the static pages are switched
            And I reload the page
                Then the static pages are switched
        """
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page for a newly created course'
        )
        self.pages_page.add_static_page()
        self.pages_page.click_edit_static_page()
        self.pages_page.set_field_val("Display Name", "First")
        self.pages_page.save()
        self.pages_page.add_static_page()
        self.pages_page.drag_and_drop()
        self.pages_page.refresh_and_wait_for_load()
        static_tab_titles = self.pages_page.static_tab_titles
        self.assertEqual(
            static_tab_titles,
            ['Empty', 'First'],
            'Order should be:["Empty", "First] but getting {} from the page'.format(static_tab_titles)
        )

    def test_user_can_reorder_builtin_tabs(self):
        """
        Scenario: Users can reorder built-in pages
            Given I have opened the pages page in a new course
                Then the built-in pages are in the default order
            When I drag the first page to the last
                Then the built-in pages are switched
            And I reload the page
                Then the built-in pages are switched
        """
        default_order = ['Home', 'Course', 'Discussion', 'Wiki', 'Progress']
        new_order = ['Home', 'Course', 'Wiki', 'Progress', 'Discussion']
        self.assertEqual(
            self.pages_page.built_in_page_titles,
            default_order,
            'Tabs are not in the default order'
        )
        self.pages_page.drag_and_drop(default_tab=True)
        built_in_page_titles = self.pages_page.built_in_page_titles
        self.assertEqual(
            built_in_page_titles,
            new_order,
            'Tabs are not in the new order'
        )
        self.pages_page.refresh_and_wait_for_load()
        self.assertEqual(
            built_in_page_titles,
            new_order,
            'Tabs are not in the new order'
        )

    def test_users_can_toggle_visibility(self):
        """
        Scenario: Users can toggle visibility on hideable pages
        Given I have opened the pages page in a new course
            Then I should see the "wiki" page as "visible"
        When I toggle the visibility of the "wiki" page
            Then I should see the "wiki" page as "hidden"
        And I reload the page
            Then I should see the "wiki" page as "hidden"
        When I toggle the visibility of the "wiki" page
            Then I should see the "wiki" page as "visible"
        And I reload the page
            Then I should see the "wiki" page as "visible"
        """
        tab = 'wiki'
        self.assertTrue(self.pages_page.is_tab_visible(tab))
        self.pages_page.toggle_tab(tab)
        self.assertFalse(self.pages_page.is_tab_visible(tab))
        self.pages_page.refresh_and_wait_for_load()
        self.assertFalse(self.pages_page.is_tab_visible(tab))
        self.pages_page.toggle_tab(tab)
        self.assertTrue(self.pages_page.is_tab_visible(tab))
        self.pages_page.refresh_and_wait_for_load()
        self.assertTrue(self.pages_page.is_tab_visible(tab))

    def test_default_order_with_static_pages(self):
        """
        Scenario: Users can reorder built-in pages amongst static pages
        Given I have created two different static pages
            Then the pages are in the default order
        """
        expected_order = ['Home', 'Course', 'Discussion', 'Wiki', 'Progress', 'First', 'Empty']
        self.assertFalse(
            self.pages_page.is_static_page_present(),
            'Static tab should not be present on the page for a newly created course'
        )
        self.pages_page.add_static_page()
        self.pages_page.click_edit_static_page()
        self.pages_page.set_field_val("Display Name", "First")
        self.pages_page.save()
        self.pages_page.add_static_page()
        tab_names = self.pages_page.built_in_page_titles + self.pages_page.static_tab_titles
        self.assertEqual(tab_names, expected_order)
