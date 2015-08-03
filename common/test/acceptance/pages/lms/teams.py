# -*- coding: utf-8 -*-
"""
Teams pages.
"""

from .course_page import CoursePage
from .discussion import InlineDiscussionPage
from ..common.paging import PaginatedUIMixin


TOPIC_CARD_CSS = 'div.wrapper-card-core'
BROWSE_BUTTON_CSS = 'a.nav-item[data-index="1"]'
TEAMS_LINK_CSS = '.action-view'
TEAMS_HEADER_CSS = '.teams-header'


class TeamsPage(CoursePage):
    """
    Teams page/tab.
    """
    url_path = "teams"

    def is_browser_on_page(self):
        """ Checks if teams page is being viewed """
        return self.q(css='body.view-teams').present

    def get_body_text(self):
        """ Returns the current dummy text. This will be changed once there is more content on the page. """
        main_page_content_css = '.page-content-main'
        self.wait_for(
            lambda: len(self.q(css=main_page_content_css).text) == 1,
            description="Body text is present"
        )
        return self.q(css=main_page_content_css).text[0]

    def browse_topics(self):
        """ View the Browse tab of the Teams page. """
        self.q(css=BROWSE_BUTTON_CSS).click()


class BrowseTopicsPage(CoursePage, PaginatedUIMixin):
    """
    The 'Browse' tab of the Teams page.
    """

    url_path = "teams/#browse"

    def is_browser_on_page(self):
        """Check if the Browse tab is being viewed."""
        button_classes = self.q(css=BROWSE_BUTTON_CSS).attrs('class')
        if len(button_classes) == 0:
            return False
        return 'is-active' in button_classes[0]

    @property
    def topic_cards(self):
        """Return a list of the topic cards present on the page."""
        return self.q(css=TOPIC_CARD_CSS).results

    def browse_teams_for_topic(self, topic_name):
        """
        Show the teams list for `topic_name`.
        """
        self.q(css=TEAMS_LINK_CSS).filter(
            text='View Teams in the {topic_name} Topic'.format(topic_name=topic_name)
        )[0].click()
        self.wait_for_ajax()


class BrowseTeamsPage(CoursePage, PaginatedUIMixin):
    """
    The paginated UI for browsing teams within a Topic on the Teams
    page.
    """
    def __init__(self, browser, course_id, topic):
        """
        Set up `self.url_path` on instantiation, since it dynamically
        reflects the current topic.  Note that `topic` is a dict
        representation of a topic following the same convention as a
        course module's topic.
        """
        super(BrowseTeamsPage, self).__init__(browser, course_id)
        self.topic = topic
        self.url_path = "teams/#topics/{topic_id}".format(topic_id=self.topic['id'])

    def is_browser_on_page(self):
        """Check if we're on the teams list page for a particular topic."""
        has_correct_url = self.url.endswith(self.url_path)
        teams_list_view_present = self.q(css='.teams-main').present
        return has_correct_url and teams_list_view_present

    @property
    def header_topic_name(self):
        """Get the topic name displayed by the page header"""
        return self.q(css=TEAMS_HEADER_CSS + ' .page-title')[0].text

    @property
    def header_topic_description(self):
        """Get the topic description displayed by the page header"""
        return self.q(css=TEAMS_HEADER_CSS + ' .page-description')[0].text

    @property
    def team_cards(self):
        """Get all the team cards on the page."""
        return self.q(css='.team-card')


class TeamPage(CoursePage, PaginatedUIMixin):
    """
    The page for a specific Team within the Teams tab
    """
    def __init__(self, browser, course_id, team):
        """
        Set up `self.url_path` on instantiation, since it dynamically
        reflects the current topic.  Note that `topic` is a dict
        representation of a topic following the same convention as a
        course module's topic.
        """
        super(TeamPage, self).__init__(browser, course_id)
        self.team = team
        self.url_path = "teams/#teams/{topic_id}/{team_id}".format(
            topic_id=self.team['topic_id'], team_id=self.team['id']
        )

    def is_browser_on_page(self):
        """Check if we're on the teams list page for a particular team."""
        has_correct_url = self.url.endswith(self.url_path)
        # The "teams-main" class is not unique to this view, but currently there is nothing else on the
        # page except for the discussion module.
        team_view_present = self.q(css='.teams-main').present
        return has_correct_url and team_view_present

    @property
    def discussion_id(self):
        """Get the id of the discussion module on the page"""
        return self.q(css='div.discussion-module').attrs('data-discussion-id')[0]

    @property
    def discussion_page(self):
        """Get the discussion as a bok_choy page object"""
        if not hasattr(self, '_discussion_page'):
            # pylint: disable=attribute-defined-outside-init
            self._discussion_page = InlineDiscussionPage(self.browser, self.discussion_id)
        return self._discussion_page
