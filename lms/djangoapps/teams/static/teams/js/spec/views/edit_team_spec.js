define([
    'jquery',
    'underscore',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'common/js/spec_helpers/page_helpers',
    'teams/js/views/edit_team',
    'teams/js/models/team',
    'teams/js/spec_helpers/team_spec_helpers'
], function ($, _, Backbone, AjaxHelpers, PageHelpers, TeamEditView, TeamModel, TeamSpecHelpers) {
    'use strict';

    describe('CreateEditTeam', function() {
        var teamsUrl = '/api/team/v0/teams/',
            createTeamData = {
                id: null,
                name: 'TeamName',
                course_id: TeamSpecHelpers.testCourseID,
                topic_id: TeamSpecHelpers.testTopicID,
                date_created: '',
                description: 'TeamDescription',
                country: 'US',
                language: 'en',
                membership: [],
                last_activity_at: ''
            },
            editTeamData = {
                name: 'UpdatedAvengers',
                description: 'We do not discuss about avengers.',
                country: 'US',
                language: 'en'
            },
            verifyValidation = function (requests, teamEditView, fieldsData) {
                _.each(fieldsData, function (fieldData) {
                    teamEditView.$(fieldData[0]).val(fieldData[1]);
                });

                teamEditView.$('.create-team.form-actions .action-primary').click();

                var message = teamEditView.$('.wrapper-msg');
                expect(message.hasClass('is-hidden')).toBeFalsy();
                var actionMessage = (
                    teamAction === 'create' ? 'Your team could not be created.' : 'Your team could not be updated.'
                );
                expect(message.find('.title').text().trim()).toBe(actionMessage);
                expect(message.find('.copy').text().trim()).toBe(
                    'Check the highlighted fields below and try again.'
                );

                _.each(fieldsData, function (fieldData) {
                    if (fieldData[2] === 'error') {
                        expect(teamEditView.$(fieldData[0].split(' ')[0] + '.error').length).toBe(1);
                    } else if (fieldData[2] === 'success') {
                        expect(teamEditView.$(fieldData[0].split(' ')[0] + '.error').length).toBe(0);
                    }
                });

                AjaxHelpers.expectNoRequests(requests);

            },
            editTeamID = 'av',
            teamAction;

        var createEditTeamView = function () {
            var testTeam = {};
            if (teamAction === 'edit') {
                testTeam = new TeamModel(
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
                action: teamAction,
                model: testTeam,
                topic: TeamSpecHelpers.createMockTopic(),
                context: TeamSpecHelpers.testContext
            }).render();
        };

        beforeEach(function () {
            setFixtures('<div class="teams-content"></div>');
            PageHelpers.preventBackboneChangingUrl();
            spyOn(Backbone.history, 'navigate');
        });

        var assertFormRendersCorrectly = function() {
            var fieldClasses = [
                    '.u-field-name',
                    '.u-field-description',
                    '.u-field-optional_description',
                    '.u-field-language',
                    '.u-field-country'
                ],
                teamEditView = createEditTeamView();

            _.each(fieldClasses, function (fieldClass) {
                expect(teamEditView.$el.find(fieldClass).length).toBe(1);
            });

            expect(teamEditView.$('.create-team.form-actions .action-primary').length).toBe(1);
            expect(teamEditView.$('.create-team.form-actions .action-cancel').length).toBe(1);

            if (teamAction === 'edit') {
                expect(teamEditView.$el.find('.u-field-name input').val()).toBe('Avengers');
                expect(teamEditView.$el.find('.u-field-description textarea').val()).toBe('Team of dumbs');
                expect(teamEditView.$el.find('.u-field-language select option:selected').text()).toBe('English');
                expect(teamEditView.$el.find('.u-field-country select option:selected').text()).toBe('United States');
            }
        };

        var requestMethod = function() {
          return teamAction === 'create' ? 'POST' : 'PATCH';
        };

        var assertTeamCreateUpdateInfo = function(that, teamsData, teamsUrl, expectedUrl) {
            var requests = AjaxHelpers.requests(that),
                teamEditView = createEditTeamView();

            teamEditView.$('.u-field-name input').val(teamsData.name);
            teamEditView.$('.u-field-textarea textarea').val(teamsData.description);
            teamEditView.$('.u-field-language select').val(teamsData.language).attr('selected', 'selected');
            teamEditView.$('.u-field-country select').val(teamsData.country).attr('selected', 'selected');

            teamEditView.$('.create-team.form-actions .action-primary').click();

            AjaxHelpers.expectJsonRequest(requests, requestMethod(), teamsUrl, teamsData);
            AjaxHelpers.respondWithJson(requests, _.extend({}, teamsData, teamAction === 'create' ? {id: '123'} : {}));

            expect(teamEditView.$('.create-team.wrapper-msg .copy').text().trim().length).toBe(0);
            expect(Backbone.history.navigate.calls[0].args).toContain(expectedUrl);
        };

        var assertValidationMessagesWhenFieldsEmpty = function(that) {
            var requests = AjaxHelpers.requests(that),
                teamEditView = createEditTeamView();

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
        };

        var assertValidationMessagesWhenInvalidData = function(that) {
            var requests = AjaxHelpers.requests(that),
                teamEditView = createEditTeamView(),
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
        };

        var assertShowMessageOnError = function(that, teamsData, teamsUrl, errorCode) {
            var teamEditView = createEditTeamView(),
                requests = AjaxHelpers.requests(that);

            teamEditView.$('.u-field-name input').val(teamsData.name);
            teamEditView.$('.u-field-textarea textarea').val(teamsData.description);

            teamEditView.$('.create-team.form-actions .action-primary').click();

            if (teamAction === 'create') {
                teamsData.country = '';
                teamsData.language = '';
            }
            AjaxHelpers.expectJsonRequest(requests, requestMethod(), teamsUrl, teamsData);

            if (errorCode < 500) {
                AjaxHelpers.respondWithError(
                        requests,
                        errorCode,
                        {'user_message': 'User message', 'developer_message': 'Developer message'}
                );
                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe('User message');
            } else {
                AjaxHelpers.respondWithError(requests);
                expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe('An error occurred. Please try again.');
            }
        };

        var assertRedirectsToCorrectUrlOnCancel = function(expectedUrl) {
            var teamEditView = createEditTeamView();
            teamEditView.$('.create-team.form-actions .action-cancel').click();
            expect(Backbone.history.navigate.calls[0].args).toContain(expectedUrl);
        };

        describe('NewTeam', function () {

            beforeEach(function() {
                teamAction = 'create';
            });

            it('can render itself correctly', function () {
                assertFormRendersCorrectly();
            });

            it('can create a team', function () {
                assertTeamCreateUpdateInfo(
                    this, createTeamData, teamsUrl, 'teams/' + TeamSpecHelpers.testTopicID + '/123'
                );
            });

            it('shows validation error message when field is empty', function () {
                assertValidationMessagesWhenFieldsEmpty(this);
            });

            it('shows validation error message when field value length exceeded the limit', function () {
                assertValidationMessagesWhenInvalidData(this);
            });

            it('shows an error message for HTTP 500', function () {
                assertShowMessageOnError(this, createTeamData, teamsUrl, 500);
            });

            it('shows correct error message when server returns an error', function () {
                assertShowMessageOnError(this, createTeamData, teamsUrl, 400);
            });

            it('changes route on cancel click', function () {
                assertRedirectsToCorrectUrlOnCancel('topics/' + TeamSpecHelpers.testTopicID);
            });
        });

        describe('EditTeam', function () {

            beforeEach(function() {
                teamAction = 'edit';
            });

            it('can render itself correctly', function () {
                assertFormRendersCorrectly();
            });

            it('can edit a team', function () {
                var copyTeamsData = _.clone(editTeamData);
                copyTeamsData.country = 'CA';
                copyTeamsData.language = 'fr';

                assertTeamCreateUpdateInfo(
                    this, copyTeamsData, teamsUrl + editTeamID + '?expand=user',
                    'teams/' + TeamSpecHelpers.testTopicID + '/' + editTeamID
                );
            });

            it('shows validation error message when field is empty', function () {
                assertValidationMessagesWhenFieldsEmpty(this);
            });

            it('shows validation error message when field value length exceeded the limit', function () {
                assertValidationMessagesWhenInvalidData(this);
            });

            it('shows an error message for HTTP 500', function () {
                assertShowMessageOnError(this, editTeamData, teamsUrl + editTeamID + '?expand=user', 500);
            });

            it('shows correct error message when server returns an error', function () {
                assertShowMessageOnError(this, editTeamData, teamsUrl + editTeamID + '?expand=user', 400);
            });

            it('changes route on cancel click', function () {
                assertRedirectsToCorrectUrlOnCancel('teams/' + TeamSpecHelpers.testTopicID + '/' + editTeamID);
            });
        });
    });
});
