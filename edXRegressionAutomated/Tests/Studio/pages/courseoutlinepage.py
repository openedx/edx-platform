from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys
from ...LMS.pages.courseware import CoursewarePage
from unitpage import UnitsPage

class CourseOutlinePage(PageObject):
    """
    Course Outline page of Auto course
    """
    url = None

    def is_browser_on_page(self):
        return 'course outline' in self.browser.title.lower()

    def click_course_link(self):
        # Click course link

        self.q(css='.course-link').first.click()
        CourseOutlinePage(self.browser).wait_for_page()

    def delete_sections(self):
        # Delete all sections on the page

        delete_section_css = self.q(css='.icon.fa.fa-trash-o')
        delete_section_confirmation = self.q(css='.button.action-primary')
        if delete_section_css.is_present():
            for items in delete_section_css:
                items.click()
                self.wait_for_element_presence('.button.action-primary', 'Delete pop up')
                delete_section_confirmation.click()
                self.wait_for_ajax()
        else:
            self.wait_for_element_presence('.add-section p', 'All sections')

    def click_view_live_button(self):
        # Verify view live button

        self.q(css='.view-live-button').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        CoursewarePage(self.browser).wait_for_page()

    def add_new_section_main_button(self, new_name):
        # Click Add section button that is next to View Live and Collapse/Expand buttons
        # Make sure there are no already added sections

        self.wait_for_element_presence('.nav-item a.button.button-new', 'Section button')
        self.q(css='.nav-item a.button.button-new').first.click()
        self.wait_for_element_visibility('.outline-item.outline-section', 'Added Section')
        self.q(css='.wrapper-content.wrapper').first.click()
        section_ids = self.q(css='.outline-item.outline-section').attrs('data-locator')
        id_of_section = ''
        for section_id in section_ids:
            if self.q(
                    css='.outline-item.outline-section[data-locator="' + section_id
                            + '"] .section-title.item-title.xblock-field-value.incontext-editor-value').text[0] \
                    == "Section":
                id_of_section = section_id
        self.q(css='.outline-item.outline-section[data-locator="' + id_of_section
                   + '"] .icon.fa.fa-pencil').first.click()
        self.browser.find_element_by_css_selector('.outline-item.outline-section[data-locator="' + id_of_section
                                                  + '"] input').send_keys(new_name + Keys.ENTER)
        self.wait_for_element_presence('.xblock-field-input.incontext-editor-input[value="' + new_name
                                       + '"]', 'Section Button')


    def add_new_subsection(self, new_name):
        # Click Add a new subsection (pre req add a new section)

        self.wait_for_element_presence('.add-subsection.add-item a.button.button-new', 'Subsection button')
        self.q(css='.add-subsection.add-item a.button.button-new').first.click()
        self.wait_for_element_visibility('input[class="xblock-field-input incontext-editor-input"][value="Subsection"]',
                                         'Added Subsection not found')
        self.q(css='.wrapper-content.wrapper').first.click()
        sub_section_ids = self.q(css='.outline-item.outline-subsection').attrs('data-locator')
        id_of_subsection = ''
        for sub_section_id in sub_section_ids:
            if self.q(css='.outline-item.outline-subsection[data-locator="' + sub_section_id
                    + '"] .subsection-title.item-title.xblock-field-value.incontext-editor-value').text[0] \
                    == "Subsection":
                id_of_subsection = sub_section_id
        self.q(css='.outline-item.outline-subsection[data-locator="' + id_of_subsection
                   + '"] .icon.fa.fa-pencil').first.click()
        self.browser.find_element_by_css_selector('.outline-item.outline-subsection[data-locator="' + id_of_subsection
                                                  + '"] input').send_keys(new_name + Keys.ENTER)
        self.wait_for_element_presence('.xblock-field-input.incontext-editor-input[value="' + new_name
                                       + '"]', 'Section Button')

    def add_new_unit(self):
        # Click Add New Unit button

        self.wait_for_element_presence('.add-unit.add-item a.button.button-new', 'Unit button')
        self.q(css='.add-unit.add-item a.button.button-new').first.click()
        UnitsPage(self.browser).wait_for_page()
