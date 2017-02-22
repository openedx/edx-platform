# -*- coding: utf-8 -*-
"""
Teams pages.
"""

from common.test.acceptance.pages.lms.course_page import CoursePage
from common.test.acceptance.pages.lms.discussion import InlineDiscussionPage
from common.test.acceptance.pages.common.paging import PaginatedUIMixin
from common.test.acceptance.pages.common.utils import confirm_prompt, click_css

from common.test.acceptance.pages.lms.fields import FieldsMixin


TOPIC_CARD_CSS = 'div.wrapper-card-core'
CARD_TITLE_CSS = 'h3.card-title'
MY_TEAMS_BUTTON_CSS = '.nav-item[data-index="0"]'
BROWSE_BUTTON_CSS = '.nav-item[data-index="1"]'
TEAMS_LINK_CSS = '.action-view'
TEAMS_HEADER_CSS = '.teams-header'
CREATE_TEAM_LINK_CSS = '.create-team'


class TeamCardsMixin(object):
    """Provides common operations on the team card component."""

    def _bounded_selector(self, css):
        """Bind the CSS to a particular tabpanel (e.g. My Teams or Browse)."""
        return '{tabpanel_id} {css}'.format(tabpanel_id=getattr(self, 'tabpanel_id', ''), css=css)

    def view_first_team(self):
        """Click the 'view' button of the first team card on the page."""
        self.q(css=self._bounded_selector('a.action-view')).first.click()

    @property
    def team_cards(self):
        """Get all the team cards on the page."""
        return self.q(css=self._bounded_selector('.team-card'))

    @property
    def team_names(self):
        """Return the names of each team on the page."""
        return self.q(css=self._bounded_selector('h3.card-title')).map(lambda e: e.text).results

    @property
    def team_descriptions(self):
        """Return the names of each team on the page."""
        return self.q(css=self._bounded_selector('p.card-description')).map(lambda e: e.text).results

    @property
    def team_memberships(self):
        """Return the team memberships text for each card on the page."""
        return self.q(css=self._bounded_selector('.member-count')).map(lambda e: e.text).results


class BreadcrumbsMixin(object):
    """Provides common operations on teams page breadcrumb links."""

    @property
    def header_page_breadcrumbs(self):
        """Get the page breadcrumb text displayed by the page header"""
        return self.q(css='.page-header .breadcrumbs')[0].text

    def click_all_topics(self):
        """ Click on the "All Topics" breadcrumb """
        self.q(css='a.nav-item').filter(text='All Topics')[0].click()

    def click_specific_topic(self, topic):
        """ Click on the breadcrumb for a specific topic """
        self.q(css='a.nav-item').filter(text=topic)[0].click()


class TeamsPage(CoursePage, BreadcrumbsMixin):
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

    def active_tab(self):
        """ Get the active tab. """
        return self.q(css='.is-active').attrs('data-url')[0]

    def browse_topics(self):
        """ View the Browse tab of the Teams page. """
        self.q(css=BROWSE_BUTTON_CSS).click()

    def verify_team_count_in_first_topic(self, expected_count):
        """
        Verify that the team count on the first topic card in the topic list is correct
        (browse topics page).
        """
        self.wait_for(
            lambda: self.q(css='.team-count')[0].text == "0 Teams" if expected_count == 0 else "1 Team",
            description="Team count text on topic is wrong"
        )

    def verify_topic_team_count(self, expected_count):
        """ Verify the number of teams listed on the topic page (browse teams within topic). """
        self.wait_for(
            lambda: len(self.q(css='.team-card')) == expected_count,
            description="Expected number of teams is wrong"
        )

    def verify_my_team_count(self, expected_count):
        """ Verify the number of teams on 'My Team'. """

        # Click to "My Team" and verify that it contains the expected number of teams.
        self.q(css=MY_TEAMS_BUTTON_CSS).click()
        self.wait_for_ajax()
        self.wait_for(
            lambda: len(self.q(css='.team-card')) == expected_count,
            description="Expected number of teams is wrong"
        )

    def click_all_topics(self):
        """ Click on the "All Topics" breadcrumb """
        self.q(css='a.nav-item').filter(text='All Topics')[0].click()

    def click_specific_topic(self, topic):
        """ Click on the breadcrumb for a specific topic """
        self.q(css='a.nav-item').filter(text=topic)[0].click()

    @property
    def warning_message(self):
        """Return the text of the team warning message."""
        return self.q(css='.warning').results[0].text


class MyTeamsPage(CoursePage, PaginatedUIMixin, TeamCardsMixin):
    """
    The 'My Teams' tab of the Teams page.
    """

    url_path = "teams/#my-teams"
    tabpanel_id = '#tabpanel-my-teams'

    def is_browser_on_page(self):
        """Check if the "My Teams" tab is being viewed."""
        button_classes = self.q(css=MY_TEAMS_BUTTON_CSS).attrs('class')
        if len(button_classes) == 0:
            return False
        return 'is-active' in button_classes[0]


class BrowseTopicsPage(CoursePage, PaginatedUIMixin):
    """
    The 'Browse' tab of the Teams page.
    """

    url_path = "teams/#browse"

    def is_browser_on_page(self):
        """Check if the Browse tab is being viewed."""
        # First off, you need to make sure that you're on the Teams page.
        if not self.q(css='.teams-main').visible:
            return False
        button_classes = self.q(css=BROWSE_BUTTON_CSS).attrs('class')
        if len(button_classes) == 0:
            return False
        return 'is-active' in button_classes[0]

    @property
    def topic_cards(self):
        """Return a list of the topic cards present on the page."""
        return self.q(css=TOPIC_CARD_CSS).results

    @property
    def topic_names(self):
        """Return a list of the topic names present on the page."""
        return self.q(css='#tabpanel-browse ' + CARD_TITLE_CSS).map(lambda e: e.text).results

    @property
    def topic_descriptions(self):
        """Return a list of the topic descriptions present on the page."""
        return self.q(css='p.card-description').map(lambda e: e.text).results

    def browse_teams_for_topic(self, topic_name):
        """
        Show the teams list for `topic_name`.
        """
        self.q(css=TEAMS_LINK_CSS).filter(
            text='View Teams in the {topic_name} Topic'.format(topic_name=topic_name)
        )[0].click()
        self.wait_for_ajax()

    def sort_topics_by(self, sort_order):
        """Sort the list of topics by the given `sort_order`."""
        self.q(
            css='#paging-header-select option[value={sort_order}]'.format(sort_order=sort_order)
        ).click()
        self.wait_for_ajax()


class BaseTeamsPage(CoursePage, PaginatedUIMixin, TeamCardsMixin, BreadcrumbsMixin):
    """
    The paginated UI for browsing teams within a Topic on the Teams
    page.
    """
    def __init__(self, browser, course_id, topic):
        """
        Note that `topic` is a dict representation of a topic following
        the same convention as a course module's topic.
        """
        super(BaseTeamsPage, self).__init__(browser, course_id)
        self.browser = browser
        self.course_id = course_id
        self.topic = topic

    def is_browser_on_page(self):
        """Check if we're on a teams list page for a particular topic."""
        has_correct_url = self.url.endswith(self.url_path)
        teams_list_view_present = self.q(css='.teams-main').present
        return has_correct_url and teams_list_view_present

    @property
    def header_name(self):
        """Get the topic name displayed by the page header"""
        return self.q(css=TEAMS_HEADER_CSS + ' .page-title')[0].text

    @property
    def header_description(self):
        """Get the topic description displayed by the page header"""
        return self.q(css=TEAMS_HEADER_CSS + ' .page-description')[0].text

    @property
    def sort_order(self):
        """Return the current sort order on the page."""
        return self.q(
            css='#paging-header-select option'
        ).filter(
            lambda e: e.is_selected()
        ).results[0].text.strip()

    @property
    def team_names(self):
        """Get all the team names on the page."""
        return self.q(css=CARD_TITLE_CSS).map(lambda e: e.text).results

    def click_create_team_link(self):
        """ Click on create team link."""
        query = self.q(css=CREATE_TEAM_LINK_CSS)
        if query.present:
            query.first.click()

        # This will bring you to the team management page
        team_management_page = TeamManagementPage(self.browser, self.course_id, self.topic)
        team_management_page.wait_for_page()

    def click_search_team_link(self):
        """ Click on create team link."""
        query = self.q(css='.search-team-descriptions')
        if query.present:
            query.first.click()
            self.wait_for_ajax()

    def click_browse_all_teams_link(self):
        """ Click on browse team link."""
        query = self.q(css='.browse-teams')
        if query.present:
            query.first.click()
            self.wait_for_ajax()

    def sort_teams_by(self, sort_order):
        """Sort the list of teams by the given `sort_order`."""
        self.q(
            css='#paging-header-select option[value={sort_order}]'.format(sort_order=sort_order)
        ).click()
        self.wait_for_ajax()

    @property
    def _showing_search_results(self):
        """
        Returns true if showing search results.
        """
        return self.header_description.startswith(u"Showing results for")

    def search(self, string):
        """
        Searches for the specified string, and returns a SearchTeamsPage
        representing the search results page.
        """
        self.q(css='.search-field').first.fill(string)
        self.q(css='.action-search').first.click()
        self.wait_for_ajax()
        self.wait_for(
            lambda: self._showing_search_results,
            description="Showing search results"
        )
        page = SearchTeamsPage(self.browser, self.course_id, self.topic)
        page.wait_for_page()
        return page


class BrowseTeamsPage(BaseTeamsPage):
    """
    The paginated UI for browsing teams within a Topic on the Teams
    page.
    """
    def __init__(self, browser, course_id, topic):
        super(BrowseTeamsPage, self).__init__(browser, course_id, topic)
        self.url_path = "teams/#topics/{topic_id}".format(topic_id=self.topic['id'])


class SearchTeamsPage(BaseTeamsPage):
    """
    The paginated UI for showing team search results.
    page.
    """
    def __init__(self, browser, course_id, topic):
        super(SearchTeamsPage, self).__init__(browser, course_id, topic)
        self.url_path = "teams/#topics/{topic_id}/search".format(topic_id=self.topic['id'])


class TeamManagementPage(CoursePage, FieldsMixin, BreadcrumbsMixin):
    """
    Team page for creation, editing, and deletion.
    """
    def __init__(self, browser, course_id, topic):
        """
        Set up `self.url_path` on instantiation, since it dynamically
        reflects the current topic.  Note that `topic` is a dict
        representation of a topic following the same convention as a
        course module's topic.
        """
        super(TeamManagementPage, self).__init__(browser, course_id)
        self.topic = topic
        self.url_path = "teams/#topics/{topic_id}/create-team".format(topic_id=self.topic['id'])

    def is_browser_on_page(self):
        """Check if we're on the create team page for a particular topic."""
        fields_css = '.team-edit-fields'
        button_sr_css = '.action.action-primary > .sr'
        return self.q(css=fields_css).present and self.q(css=button_sr_css).visible

    @property
    def header_page_name(self):
        """Get the page name displayed by the page header"""
        return self.q(css='.page-header .page-title')[0].text

    @property
    def header_page_description(self):
        """Get the page description displayed by the page header"""
        return self.q(css='.page-header .page-description')[0].text

    @property
    def validation_message_text(self):
        """Get the error message text"""
        return self.q(css='.create-team.wrapper-msg .copy')[0].text

    def create_team(self, name='Team Name', description='Team description.'):
        """Create a new team"""
        self.value_for_text_field(field_id='name', value=name, press_enter=False)
        self.set_value_for_textarea_field(
            field_id='description',
            value=description
        )
        self.submit_form()

    def submit_form(self):
        """Click on create team button"""
        self.q(css='.create-team .action-primary').first.click()
        self.wait_for_ajax()

    def cancel_team(self):
        """Click on cancel team button"""
        self.q(css='.create-team .action-cancel').first.click()
        self.wait_for_ajax()

    @property
    def delete_team_button(self):
        """Returns the 'delete team' button."""
        return self.q(css='.action-delete').first

    def click_membership_button(self):
        """Clicks the 'edit membership' button"""
        self.q(css='.action-edit-members').first.click()
        self.wait_for_ajax()

    @property
    def membership_button_present(self):
        """Checks if the edit membership button is present"""
        return self.q(css='.action-edit-members').present


class EditMembershipPage(CoursePage):
    """
    Staff or discussion-privileged user page to remove troublesome or inactive
    students from a team
    """
    def __init__(self, browser, course_id, team):
        """
        Set up `self.url_path` on instantiation, since it dynamically
        reflects the current team.
        """
        super(EditMembershipPage, self).__init__(browser, course_id)
        self.team = team
        self.url_path = "teams/#teams/{topic_id}/{team_id}/edit-team/manage-members".format(
            topic_id=self.team['topic_id'], team_id=self.team['id']
        )

    def is_browser_on_page(self):
        """Check if we're on the team membership page for a particular team."""
        self.wait_for_ajax()

        if self.q(css='.edit-members').present:
            return True
        empty_query = self.q(css='.teams-main>.page-content>p').first
        return (
            len(empty_query.results) > 0 and
            empty_query[0].text == "This team does not have any members."
        )

    @property
    def team_members(self):
        """Returns the number of team members shown on the page."""
        return len(self.q(css='.team-member'))

    def click_first_remove(self):
        """Clicks the remove link on the first member listed."""
        self.q(css='.action-remove-member').first.click()

    def confirm_delete_membership_dialog(self):
        """Click 'delete' on the warning dialog."""
        confirm_prompt(self, require_notification=False)
        self.wait_for_ajax()

    def cancel_delete_membership_dialog(self):
        """Click 'delete' on the warning dialog."""
        confirm_prompt(self, cancel=True)


class TeamPage(CoursePage, PaginatedUIMixin, BreadcrumbsMixin):
    """
    The page for a specific Team within the Teams tab
    """
    def __init__(self, browser, course_id, team=None):
        """
        Set up `self.url_path` on instantiation, since it dynamically
        reflects the current team.
        """
        super(TeamPage, self).__init__(browser, course_id)
        self.team = team
        if self.team:
            self.url_path = "teams/#teams/{topic_id}/{team_id}".format(
                topic_id=self.team['topic_id'], team_id=self.team['id']
            )

    def is_browser_on_page(self):
        """Check if we're on the teams list page for a particular team."""
        self.wait_for_ajax()
        if self.team:
            if not self.url.endswith(self.url_path):
                return False
        return self.q(css='.teams-main .team-members').visible

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

    @property
    def team_name(self):
        """Get the team's name as displayed in the page header"""
        return self.q(css='.page-header .page-title')[0].text

    @property
    def team_description(self):
        """Get the team's description as displayed in the page header"""
        return self.q(css=TEAMS_HEADER_CSS + ' .page-description')[0].text

    @property
    def team_members_present(self):
        """Verifies that team members are present"""
        return self.q(css='.page-content-secondary .team-members .team-member').present

    @property
    def team_capacity_text(self):
        """Returns team capacity text"""
        return self.q(css='.page-content-secondary .team-capacity :last-child').text[0]

    @property
    def team_location(self):
        """ Returns team location/country. """
        return self.q(css='.page-content-secondary .team-country :last-child').text[0]

    @property
    def team_language(self):
        """ Returns team location/country. """
        return self.q(css='.page-content-secondary .team-language :last-child').text[0]

    @property
    def team_user_membership_text(self):
        """Returns the team membership text"""
        query = self.q(css='.page-content-secondary > .team-user-membership-status')
        return query.text[0] if query.present else ''

    @property
    def team_leave_link_present(self):
        """Verifies that team leave link is present"""
        return self.q(css='.leave-team-link').present

    def click_leave_team_link(self, remaining_members=0, cancel=False):
        """ Click on Leave Team link"""
        leave_team_css = '.leave-team-link'
        self.wait_for_element_visibility(leave_team_css, 'Leave Team link is visible.')
        click_css(self, leave_team_css, require_notification=False)
        confirm_prompt(self, cancel, require_notification=False)

        if cancel is False:
            self.wait_for(
                lambda: self.join_team_button_present,
                description="Join Team button did not become present"
            )
            self.wait_for_capacity_text(remaining_members)

    @property
    def team_members(self):
        """Returns the number of team members in this team"""
        return len(self.q(css='.page-content-secondary .team-member'))

    def click_first_profile_image(self):
        """Clicks on first team member's profile image"""
        self.q(css='.page-content-secondary .members-info .team-member').first.click()

    @property
    def first_member_username(self):
        """Returns the username of team member"""
        return self.q(css='.page-content-secondary .tooltip-custom').text[0]

    def click_join_team_button(self, total_members=1):
        """ Click on Join Team button"""
        self.q(css='.join-team .action-primary').first.click()
        self.wait_for(
            lambda: not self.join_team_button_present,
            description="Join Team button did not go away"
        )
        self.wait_for_capacity_text(total_members)

    def wait_for_capacity_text(self, num_members, max_size=10):
        """ Wait for the team capacity text to be correct. """
        self.wait_for(
            lambda: self.team_capacity_text == self.format_capacity_text(num_members, max_size),
            description="Team capacity text is not correct"
        )

    def format_capacity_text(self, num_members, max_size):
        """ Helper method to format the expected team capacity text. """
        return '{num_members} / {max_size} {members_text}'.format(
            num_members=num_members,
            max_size=max_size,
            members_text='Member' if num_members == max_size else 'Members'
        )

    @property
    def join_team_message(self):
        """ Returns join team message """
        self.wait_for_ajax()
        return self.q(css='.join-team .join-team-message').text[0]

    @property
    def join_team_button_present(self):
        """ Returns True if Join Team button is present else False """
        return self.q(css='.join-team .action-primary').present

    @property
    def join_team_message_present(self):
        """ Returns True if Join Team message is present else False """
        return self.q(css='.join-team .join-team-message').present

    @property
    def new_post_button_present(self):
        """ Returns True if New Post button is present else False """
        return self.q(css='.discussion-module .new-post-btn').visible

    @property
    def edit_team_button_present(self):
        """ Returns True if Edit Team button is present else False """
        return self.q(css='.form-actions .action-edit-team').present

    def click_edit_team_button(self):
        """ Click on Edit Team button"""
        self.q(css='.form-actions .action-edit-team').first.click()
