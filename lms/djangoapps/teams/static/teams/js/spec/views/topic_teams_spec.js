define([
  'backbone',
  'underscore',
  'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
  'teams/js/views/topic_teams',
  'teams/js/spec_helpers/team_spec_helpers',
  'common/js/spec_helpers/page_helpers'
], function(Backbone, _, AjaxHelpers, TopicTeamsView, TeamSpecHelpers, PageHelpers) {
  'use strict';
  describe('Topic Teams View', function() {
    let requests, view;

    const verifyTeamsetTeamsRequest = (hasTeams) => {
      const {
        testUser: username,
        testCourseID: course_id,
        testTopicID: teamset_id,
      } = TeamSpecHelpers;
      AjaxHelpers.expectRequestURL(
        requests,
        TeamSpecHelpers.testContext.teamMembershipsUrl,
        { username, course_id, teamset_id },
      );
      AjaxHelpers.respondWithJson(
        requests,
        JSON.stringify({ count: hasTeams ? 1 : 0 }),
      );
    };

    const createTopicTeamsView = async ({
      teams,
      isInstructorManagedTopic,
      onTeamInTeamset,
      options,
    }) => new Promise((resolve) => {
      requests = AjaxHelpers.requests();
      const model = isInstructorManagedTopic
        ? TeamSpecHelpers.createMockInstructorManagedTopic()
        : TeamSpecHelpers.createMockTopic();

      view = new TopicTeamsView({
        el: '.teams-container',
        model,
        collection: teams || TeamSpecHelpers.createMockTeams({results: []}),
        context: _.extend({}, TeamSpecHelpers.testContext, options)
      });

      view.render().then(() => {
        verifyTeamsetTeamsRequest(onTeamInTeamset);
        resolve(view);
      });
    });

    /**
     * Verify whether the actions message is displayed in the element.
     * @param {TopicTeamsView} teamsView - parent element
     * @param {bool=true} showActions - should the actions be shown?
     */
    const verifyActions = function(teamsView, showActions) {
      const expectedTitle = 'Are you having trouble finding a team to join?',
        expectedMessage = 'Browse teams in other topics or search teams in this topic. ' +
          'If you still can\'t find a team to join, create a new team in this topic.',
        title = teamsView.$('.title').text().trim(),
        message = teamsView.$('.copy').text().trim();

      if (showActions === false) {
        expect(title).toBe(expectedTitle);
        expect(message).toBe(expectedMessage);
      } else {
        expect(title).not.toBe(expectedTitle);
        expect(message).not.toBe(expectedMessage);
      }
    };

    beforeEach(function() {
      setFixtures('<div class="teams-container"></div>');
      PageHelpers.preventBackboneChangingUrl();
    });

    it('can render itself', function() {
      // Unpriviledged non-staff user, not on any teams in teamset.
      // Team is not instructor managed.
      const testTeamData = TeamSpecHelpers.createMockTeamData(1, 5);

      createTopicTeamsView({
        teams: TeamSpecHelpers.createMockTeams({ results: testTeamData }),
      }).then((teamsView) => {
        const footerEl = teamsView.$('.teams-paging-footer');

        expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');
        expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2'); // eslint-disable-line no-useless-escape
        expect(footerEl).not.toHaveClass('hidden');

        TeamSpecHelpers.verifyCards(teamsView, testTeamData);
        verifyActions(teamsView);
      });
    });

    it('can browse all teams', function() {
      createTopicTeamsView().then((teamsView) => {
        spyOn(Backbone.history, 'navigate');
        teamsView.$('.browse-teams').click();
        expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe('browse');
      });
    });

    it('gives the search field focus when clicking on the search teams link', function() {
      createTopicTeamsView().then((teamsView) => {
        spyOn($.fn, 'focus').and.callThrough();
        teamsView.$('.search-teams').click();
        expect(teamsView.$('.search-field').first().focus).toHaveBeenCalled();
      });
    });

    it('can show the create team modal', function() {
      createTopicTeamsView().then((teamsView) => {
        spyOn(Backbone.history, 'navigate');
        teamsView.$('a.create-team').click();
        expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe(
          'topics/' + TeamSpecHelpers.testTopicID + '/create-team'
        );
      });
    });

    it('does not show actions for a user already in a team in the teamset', function() {
      createTopicTeamsView({
        onTeamInTeamset: true
      }).then((teamsView) => {
        verifyActions(teamsView, false);
      });
    });

    it('does not show actions for a student in an instructor managed topic', function() {
      createTopicTeamsView({
        isInstructorManagedTopic: true,
      }).then((teamsView) => {
        verifyActions(teamsView, false);
      });
    });

    it('shows actions for a privileged user already in a team', function() {
      const options = {
        userInfo: {
          privileged: true,
          staff: false
        },
      };
      createTopicTeamsView({
        options,
        onTeamInTeamset: true,
      }).then((teamsView) => {
        verifyActions(teamsView);
      });
    });

    it('shows actions for a staff user already in a team', function() {
      const options = {
        userInfo: {
          privileged: false,
          staff: true,
        },
      };
      createTopicTeamsView({
        options,
        onTeamInTeamset: true,
      }).then((teamsView) => {
        verifyActions(teamsView);
      });
    });

    /*
    // TODO: make this ready for prime time
    it('refreshes when the team membership changes', function() {
      var requests = AjaxHelpers.requests(this),
        teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
        teamsView = createTopicTeamsView({ teamMemberships: teamMemberships });
      verifyActions(teamsView);
      teamMemberships.teamEvents.trigger('teams:update', { action: 'create' });
      teamsView.render();
      AjaxHelpers.expectRequestURL(
        requests,
        'foo',
        {
          expand : 'team',
          username : 'testUser',
          course_id : TeamSpecHelpers.testCourseID,
          page : '1',
          page_size : '10'
        }
      );
      AjaxHelpers.respondWithJson(requests, {});
      verifyActions(teamsView);
    });
    */
  });
});
