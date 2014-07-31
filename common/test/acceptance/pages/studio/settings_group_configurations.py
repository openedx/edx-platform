"""
Course Group Configurations page.
"""

from .course_page import CoursePage


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
        css = 'a.group-toggle'
        self.find_css(css).first.click()

    def add_group(self):
        """
        Add new group.
        """
        css = 'button.action-add-group'
        self.find_css(css).first.click()

    def get_text(self, css):
        """
        Return text for the defined by css locator.
        """
        return self.find_css(css).first.text[0]

    def click_outline_anchor(self):
        """
        Click on the `Course Outline` link.
        """
        css = 'p.group-configuration-usage-text a'
        self.find_css(css).first.click()

    def click_unit_anchor(self, index=0):
        """
        Click on the link to the unit.
        """
        css = 'li.group-configuration-usage-unit a'
        self.find_css(css).nth(index).click()

    def edit(self):
        """
        Open editing view for the group configuration.
        """
        css = '.action-edit .edit'
        self.find_css(css).first.click()

    def save(self):
        """
        Save group configuration.
        """
        css = '.action-primary'
        self.find_css(css).first.click()
        self.page.wait_for_ajax()

    def cancel(self):
        """
        Cancel group configuration.
        """
        css = '.action-secondary'
        self.find_css(css).first.click()

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
        css = '.group-configuration-name-input'
        self.find_css(css).first.fill(value)

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
        css = '.group-configuration-description-input'
        self.find_css(css).first.fill(value)

    @property
    def groups(self):
        """
        Return list of groups.
        """
        css = '.group'

        def group_selector(group_index):
            return self.get_selector('.group-{} '.format(group_index))

        return [Group(self.page, group_selector(index)) for index, element in enumerate(self.find_css(css))]

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
