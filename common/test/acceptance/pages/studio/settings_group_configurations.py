"""
Course Group Configurations page.
"""

from .course_page import CoursePage
from .utils import confirm_prompt


class GroupConfigurationsPage(CoursePage):
    """
    Course Group Configurations page.
    """

    url_path = "group_configurations"

    def is_browser_on_page(self):
        return self.q(css='body.view-group-configurations').present

    @property
    def group_configurations(self):
        """
        Return list of the group configurations for the course.
        """
        css = '.group-configurations-list-item'
        return [GroupConfiguration(self, index) for index in xrange(len(self.q(css=css)))]

    def create(self):
        """
        Creates new group configuration.
        """
        self.q(css=".new-button").first.click()

    @property
    def no_group_configuration_message_is_present(self):
        return self.q(css='.wrapper-content .no-group-configurations-content').present

    @property
    def no_group_configuration_message_text(self):
        return self.q(css='.wrapper-content .no-group-configurations-content').text[0]


class GroupConfiguration(object):
    """
    Group Configuration wrapper.
    """

    def __init__(self, page, index):
        self.page = page
        self.SELECTOR = '.group-configurations-list-item-{}'.format(index)
        self.index = index

    def get_selector(self, css=''):
        return ' '.join([self.SELECTOR, css])

    def find_css(self, selector):
        """
        Find elements as defined by css locator.
        """
        return self.page.q(css=self.get_selector(css=selector))

    def toggle(self):
        """
        Expand/collapse group configuration.
        """
        self.find_css('a.group-toggle').first.click()

    @property
    def is_expanded(self):
        """
        Group configuration usage information is expanded.
        """
        return self.find_css('a.group-toggle.hide-groups').present

    def add_group(self):
        """
        Add new group.
        """
        self.find_css('button.action-add-group').first.click()

    def get_text(self, css):
        """
        Return text for the defined by css locator.
        """
        return self.find_css(css).first.text[0]

    def click_outline_anchor(self):
        """
        Click on the `Course Outline` link.
        """
        self.find_css('p.group-configuration-usage-text a').first.click()

    def click_unit_anchor(self, index=0):
        """
        Click on the link to the unit.
        """
        self.find_css('li.group-configuration-usage-unit a').nth(index).click()

    def edit(self):
        """
        Open editing view for the group configuration.
        """
        self.find_css('.action-edit .edit').first.click()

    @property
    def delete_button_is_disabled(self):
        return self.find_css('.actions .delete.is-disabled').present

    @property
    def delete_button_is_absent(self):
        return not self.find_css('.actions .delete').present

    def delete(self):
        """
        Delete the group configuration.
        """
        self.find_css('.actions .delete').first.click()
        confirm_prompt(self.page)

    def save(self):
        """
        Save group configuration.
        """
        self.find_css('.action-primary').first.click()
        self.page.wait_for_ajax()

    def cancel(self):
        """
        Cancel group configuration.
        """
        self.find_css('.action-secondary').first.click()

    @property
    def mode(self):
        """
        Return group configuration mode.
        """
        if self.find_css('.group-configuration-edit').present:
            return 'edit'
        elif self.find_css('.group-configuration-details').present:
            return 'details'

    @property
    def id(self):
        """
        Return group configuration id.
        """
        return self.get_text('.group-configuration-id .group-configuration-value')

    @property
    def validation_message(self):
        """
        Return validation message.
        """
        return self.get_text('.message-status.error')

    @property
    def usages(self):
        """
        Return list of usages.
        """
        css = '.group-configuration-usage-unit'
        return self.find_css(css).text

    @property
    def name(self):
        """
        Return group configuration name.
        """
        return self.get_text('.group-configuration-title')

    @name.setter
    def name(self, value):
        """
        Set group configuration name.
        """
        self.find_css('.group-configuration-name-input').first.fill(value)

    @property
    def description(self):
        """
        Return group configuration description.
        """
        return self.get_text('.group-configuration-description')

    @description.setter
    def description(self, value):
        """
        Set group configuration description.
        """
        self.find_css('.group-configuration-description-input').first.fill(value)

    @property
    def groups(self):
        """
        Return list of groups.
        """
        def group_selector(group_index):
            return self.get_selector('.group-{} '.format(group_index))

        return [Group(self.page, group_selector(index)) for index, element in enumerate(self.find_css('.group'))]

    @property
    def delete_note(self):
        """
        Return delete note for the group configuration.
        """
        return self.find_css('.wrapper-delete-button').first.attrs('data-tooltip')[0]

    @property
    def details_error_icon_is_present(self):
        return self.find_css('.wrapper-group-configuration-usages .icon-exclamation-sign').present

    @property
    def details_warning_icon_is_present(self):
        return self.find_css('.wrapper-group-configuration-usages .icon-warning-sign').present

    @property
    def details_message_is_present(self):
        return self.find_css('.wrapper-group-configuration-usages .group-configuration-validation-message').present

    @property
    def details_message_text(self):
        return self.find_css('.wrapper-group-configuration-usages .group-configuration-validation-message').text[0]

    @property
    def edit_warning_icon_is_present(self):
        return self.find_css('.wrapper-group-configuration-validation .icon-warning-sign').present

    @property
    def edit_warning_message_is_present(self):
        return self.find_css('.wrapper-group-configuration-validation .group-configuration-validation-text').present

    @property
    def edit_warning_message_text(self):
        return self.find_css('.wrapper-group-configuration-validation .group-configuration-validation-text').text[0]

    def __repr__(self):
        return "<{}:{}>".format(self.__class__.__name__, self.name)


class Group(object):
    """
    Group wrapper.
    """
    def __init__(self, page, prefix_selector):
        self.page = page
        self.prefix = prefix_selector

    def find_css(self, selector):
        """
        Find elements as defined by css locator.
        """
        return self.page.q(css=self.prefix + selector)

    @property
    def name(self):
        """
        Return the name of the group .
        """
        css = '.group-name'
        return self.find_css(css).first.text[0]

    @name.setter
    def name(self, value):
        """
        Set the name for the group.
        """
        css = '.group-name'
        self.find_css(css).first.fill(value)

    @property
    def allocation(self):
        """
        Return allocation for the group.
        """
        css = '.group-allocation'
        return self.find_css(css).first.text[0]

    def remove(self):
        """
        Remove the group.
        """
        css = '.action-close'
        return self.find_css(css).first.click()

    def __repr__(self):
        return "<{}:{}>".format(self.__class__.__name__, self.name)
