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

    def group_configurations(self):
        """
        Returns list of the group configurations for the course.
        """
        css = '.wrapper-group-configuration'
        return [GroupConfiguration(self, index) for index in xrange(len(self.q(css=css)))]


class GroupConfiguration(object):
    """
    Group Configuration wrapper.
    """

    def __init__(self, page, index):
        self.page = page
        self.SELECTOR = '.view-group-configuration-{}'.format(index)
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

    @property
    def id(self):
        """
        Returns group configuration id.
        """
        css = '.group-configuration-id .group-configuration-value'
        return self.find_css(css).first.text[0]

    @property
    def name(self):
        """
        Returns group configuration name.
        """
        css = '.group-configuration-title'
        return self.find_css(css).first.text[0]

    @property
    def description(self):
        """
        Returns group configuration description.
        """
        css = '.group-configuration-description'
        return self.find_css(css).first.text[0]

    @property
    def groups(self):
        """
        Returns list of groups.
        """
        css = '.group'

        def group_selector(config_index, group_index):
            return self.get_selector('.groups-{} .group-{} '.format(config_index, group_index))

        return [Group(self.page, group_selector(self.index, index)) for index, element in enumerate(self.find_css(css))]

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
        Returns group name.
        """
        css = '.group-name'
        return self.find_css(css).first.text[0]

    @property
    def allocation(self):
        """
        Returns allocation for the group.
        """
        css = '.group-allocation'
        return self.find_css(css).first.text[0]

    def __repr__(self):
        return "<{}:{}>".format(self.__class__.__name__, self.name)
