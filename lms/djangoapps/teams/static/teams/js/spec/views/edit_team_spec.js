define([
    'jquery',
    'underscore',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'teams/js/views/edit_team',
    'teams/js/models/team',
    'teams/js/spec_helpers/team_spec_helpers'
], function ($, _, Backbone, AjaxHelpers, TeamEditView, TeamModel, TeamSpecHelpers) {
    'use strict';

    describe('CreateEditTeam', function() {
        var teamsUrl = '/api/team/v0/teams/',
            createTeamsData = {
                id: null,
                name: "TeamName",
                is_active: null,
                course_id: "a/b/c",
                topic_id: "awesomeness",
                date_created: "",
                description: "TeamDescription",
                country: "US",
                language: "en",
                membership: []
            },
            verifyValidation = function (requests, teamEditView, fieldsData) {
                _.each(fieldsData, function (fieldData) {
                    teamEditView.$(fieldData[0]).val(fieldData[1]);
                });

                teamEditView.$('.create-team.form-actions .action-primary').click();

                var message = teamEditView.$('.wrapper-msg');
                expect(message.hasClass('is-hidden')).toBeFalsy();
                var actionMessage = teamAction === 'create' ? 'Your team could not be created!' : 'Your team could not be updated!';
                expect(message.find('.title').text().trim()).toBe(actionMessage);
                expect(message.find('.copy').text().trim()).toBe(
                    "Check the highlighted fields below and try again."
                );

                _.each(fieldsData, function (fieldData) {
                    if (fieldData[2] === 'error') {
                        expect(teamEditView.$(fieldData[0].split(" ")[0] + '.error').length).toBe(1);
                    } else if (fieldData[2] === 'success') {
                        expect(teamEditView.$(fieldData[0].split(" ")[0] + '.error').length).toBe(0);
                    }
                });

                expect(requests.length).toBe(0);
            },
            editTeamID = 'av',
            teamAction;


            var createEditTeamView = function (title, action) {
                var teamModel = {};
                if (action === 'edit') {
                    teamModel = new TeamModel(
                        {
                            id: editTeamID,
                            name: 'Avengers',
                            description: 'Team of dumbs',
                            language: 'en',
                            country: 'US',
                            membership: [],
                            url: '/api/team/v0/teams/' + editTeamID
                        },
                        {
                            parse: true
                        }
                    );
                }

                return new TeamEditView({
                    teamEvents: TeamSpecHelpers.teamEvents,
                    el: $('.teams-content'),
                    action: action,
                    primaryButtonTitle: title,
                    model: teamModel,
                    teamParams: {
                        teamsUrl: teamsUrl,
                        courseID: "a/b/c",
                        topicID: 'awesomeness',
                        topicName: 'Awesomeness',
                        languages: [['aa', 'Afar'], ['fr', 'French'], ['en', 'English']],
                        countries: [['af', 'Afghanistan'], ['CA', 'Canada'], ['US', 'United States']],
                        teamsDetailUrl: teamModel.url
                    }
                }).render();
            };

            beforeEach(function () {
                setFixtures('<div class="teams-content"></div>');
                spyOn(Backbone.history, 'navigate');
            });

        describe('NewTeam', function () {

            it('can render itself correctly', function () {
                var fieldClasses = [
                        '.u-field-name',
                        '.u-field-description',
                        '.u-field-optional_description',
                        '.u-field-language',
                        '.u-field-country'
                    ],
                    teamEditView = createEditTeamView('Create a New Team', 'create');

                _.each(fieldClasses, function (fieldClass) {
                    expect(teamEditView.$el.find(fieldClass).length).toBe(1);
                });

                expect(teamEditView.$('.create-team.form-actions .action-primary').length).toBe(1);
                expect(teamEditView.$('.create-team.form-actions .action-cancel').length).toBe(1);
            });

            it('can create a team', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Create a New Team', 'create');

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);
                teamEditView.$('.u-field-language select').val('en').attr("selected", "selected");
                teamEditView.$('.u-field-country select').val('US').attr("selected", "selected");

                teamEditView.$('.create-team.form-actions .action-primary').click();
                AjaxHelpers.expectJsonRequest(requests, 'POST', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithJson(requests, _.extend(_.extend({}, createTeamsData), {id: '123'}));

                expect(teamEditView.$('.create-team.wrapper-msg .copy').text().trim().length).toBe(0);
                expect(Backbone.history.navigate.calls[0].args).toContain('teams/awesomeness/123');
            });

            it('shows validation error message when field is empty', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Create a New Team', 'create');
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', 'Name', 'success'],
                    ['.u-field-textarea textarea', '', 'error']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', '', 'error'],
                    ['.u-field-textarea textarea', 'description', 'success']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', '', 'error'],
                    ['.u-field-textarea textarea', '', 'error']
                ]);
            });

            it('shows validation error message when field value length exceeded the limit', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Create a New Team', 'create'),
                    teamName = new Array(500 + 1).join('$'),
                    teamDescription = new Array(500 + 1).join('$');

                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', teamName, 'error'],
                    ['.u-field-textarea textarea', 'description', 'success']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', 'name', 'success'],
                    ['.u-field-textarea textarea', teamDescription, 'error']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', teamName, 'error'],
                    ['.u-field-textarea textarea', teamDescription, 'error']
                ]);
            });

            it("shows an error message for HTTP 500", function () {
                var teamEditView = createEditTeamView('Create a New Team', 'create'),
                    requests = AjaxHelpers.requests(this);

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);

                teamEditView.$('.create-team.form-actions .action-primary').click();
                createTeamsData.country = '';
                createTeamsData.language = '';
                AjaxHelpers.expectJsonRequest(requests, 'POST', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithError(requests);

                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe("An error occurred. Please try again.");
            });

            it("shows correct error message when server returns an error", function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Create a New Team', 'create');

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);

                teamEditView.$('.create-team.form-actions .action-primary').click();
                createTeamsData.country = '';
                createTeamsData.language = '';
                AjaxHelpers.expectJsonRequest(requests, 'POST', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithError(
                    requests,
                    400,
                    {'user_message': 'User message', 'developer_message': 'Developer message'}
                );

                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe("User message");
            });

            it("changes route on cancel click", function () {
                var teamEditView = createEditTeamView('Create a New Team', 'create');
                teamEditView.$('.create-team.form-actions .action-cancel').click();
                expect(Backbone.history.navigate.calls[0].args).toContain('topics/awesomeness');
            });
        });


        describe('EditTeam', function () {

            it('can render itself correctly', function () {
                var fieldClasses = [
                        '.u-field-name',
                        '.u-field-description',
                        '.u-field-optional_description',
                        '.u-field-language',
                        '.u-field-country'
                    ],
                    teamEditView = createEditTeamView('Update', 'edit');

                _.each(fieldClasses, function (fieldClass) {
                    expect(teamEditView.$el.find(fieldClass).length).toBe(1);
                });
                expect(teamEditView.$('.wrapper-msg-fixed .copy').text().trim()).toContain('The team that you are editing has');
                expect(teamEditView.$el.find('.u-field-name input').val()).toBe('Avengers');
                expect(teamEditView.$el.find('.u-field-description textarea').val()).toBe('Team of dumbs');
                expect(teamEditView.$el.find('.u-field-language select option:selected').text()).toBe('English');
                expect(teamEditView.$el.find('.u-field-country select option:selected').text()).toBe('United States');

                expect(teamEditView.$('.create-team.form-actions .action-primary').length).toBe(1);
                expect(teamEditView.$('.create-team.form-actions .action-primary').text()).toContain('Update');
                expect(teamEditView.$('.create-team.form-actions .action-cancel').length).toBe(1);
            });

            it('can edit a team', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Update', 'edit');

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);
                teamEditView.$('.u-field-language select').val('fr').attr("selected", "selected");
                teamEditView.$('.u-field-country select').val('CA').attr("selected", "selected");

                teamEditView.$('.create-team.form-actions .action-primary').click();
                AjaxHelpers.expectJsonRequest(requests, 'PATCH', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithJson(requests, _.extend(_.extend({}, createTeamsData)));

                expect(teamEditView.$('.create-team.wrapper-msg .copy').text().trim().length).toBe(0);
                expect(Backbone.history.navigate.calls[0].args).toContain('teams/awesomeness/123');
            });

            it('shows validation error message when field is empty', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Update', 'edit');
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', 'Name', 'success'],
                    ['.u-field-textarea textarea', '', 'error']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', '', 'error'],
                    ['.u-field-textarea textarea', 'description', 'success']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', '', 'error'],
                    ['.u-field-textarea textarea', '', 'error']
                ]);
            });

            it('shows validation error message when field value length exceeded the limit', function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Update', 'edit'),
                    teamName = new Array(500 + 1).join( '$'),
                    teamDescription = new Array(500 + 1).join( '$' );

                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', teamName, 'error'],
                    ['.u-field-textarea textarea', 'description', 'success']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', 'name', 'success'],
                    ['.u-field-textarea textarea', teamDescription, 'error']
                ]);
                teamEditView.render();
                verifyValidation(requests, teamEditView, [
                    ['.u-field-name input', teamName, 'error'],
                    ['.u-field-textarea textarea', teamDescription, 'error']
                ]);
            });

            it("shows an error message for HTTP 500", function () {
                var teamEditView = createEditTeamView('Update', 'edit'),
                    requests = AjaxHelpers.requests(this);

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);

                teamEditView.$('.create-team.form-actions .action-primary').click();
                createTeamsData.country = '';
                createTeamsData.language = '';
                AjaxHelpers.expectJsonRequest(requests, 'PATCH', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithError(requests);

                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe("An error occurred. Please try again.");
            });

            it("shows correct error message when server returns an error", function () {
                var requests = AjaxHelpers.requests(this),
                    teamEditView = createEditTeamView('Update', 'edit');

                teamEditView.$('.u-field-name input').val(createTeamsData.name);
                teamEditView.$('.u-field-textarea textarea').val(createTeamsData.description);

                teamEditView.$('.create-team.form-actions .action-primary').click();
                createTeamsData.country = '';
                createTeamsData.language = '';
                AjaxHelpers.expectJsonRequest(requests, 'PATCH', teamsUrl, createTeamsData);
                AjaxHelpers.respondWithError(
                        requests,
                        400,
                        {'user_message': 'User message', 'developer_message': 'Developer message'}
                );

                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe("User message");
            });

            it("changes route on cancel click", function () {
                var teamEditView = createEditTeamView('Update', 'edit');
                teamEditView.$('.create-team.form-actions .action-cancel').click();
                expect(Backbone.history.navigate.calls[0].args).toContain('teams/awesomeness/ave');
            });
        });
    });
});
