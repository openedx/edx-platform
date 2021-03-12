define(['jquery', 'backbone', 'teams/js/teams_tab_factory', 'teams/js/views/teams_tab',
    'common/js/spec_helpers/page_helpers', 'teams/js/spec_helpers/team_spec_helpers'],
    function($, Backbone, TeamsTabFactory, TeamsTabView, PageHelpers, TeamSpecHelpers) {
        'use strict';

        describe('Teams Tab Factory', function() {
            var initializeTeamsTabFactory = function(hasOpenTopic, hasPublicManagedTopic) {
                var context = TeamSpecHelpers.createMockContext();
                context.hasOpenTopic = hasOpenTopic;
                context.hasPublicManagedTopic = hasPublicManagedTopic;
                TeamsTabFactory(context);
            };

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
                PageHelpers.preventBackboneChangingUrl();
            });

            afterEach(function() {
                Backbone.history.stop();
                $(document).off('ajaxError', TeamsTabView.prototype.errorHandler);
            });

            describe('can render the "Teams" tab', function() {
                it('when there are no private or open teamsets', function() {
                    initializeTeamsTabFactory(false, false);
                    expect($('.teams-content').text()).toContain('See all teams you belong to');
                    expect($('.teams-content').text()).not.toContain('and all public teams in your course');
                    expect($('.teams-content').text()).not.toContain('Join an open public team');
                });
                it('when there are no open teamsets but there are public teamsets', function() {
                    initializeTeamsTabFactory(false, true);
                    expect($('.teams-content').text()).toContain('See all teams you belong to');
                    expect($('.teams-content').text()).toContain('and all public teams in your course');
                    expect($('.teams-content').text()).not.toContain('Join an open public team');
                });
                it('when there are open teamsets but no public teamsets', function() {
                    initializeTeamsTabFactory(true, false);
                    expect($('.teams-content').text()).toContain('See all teams you belong to');
                    expect($('.teams-content').text()).toContain('and all public teams in your course');
                    expect($('.teams-content').text()).toContain('Join an open public team');
                });
                it('when there are both open and public teamsets', function() {
                    initializeTeamsTabFactory(true, true);
                    expect($('.teams-content').text()).toContain('See all teams you belong to');
                    expect($('.teams-content').text()).toContain('and all public teams in your course');
                    expect($('.teams-content').text()).toContain('Join an open public team');
                });
            });
        });
    }
);
