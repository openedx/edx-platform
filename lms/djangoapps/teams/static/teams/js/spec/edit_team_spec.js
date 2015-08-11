define([
    'jquery',
    'underscore',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'teams/js/views/edit_team'
], function ($, _, Backbone, AjaxHelpers, TeamEditView) {
    'use strict';

    describe('EditTeam', function () {
        var teamEditView,
            teamsUrl = '/api/team/v0/teams/',
            teamsData = {
                id: null,
                name: "TeamName",
                is_active: null,
                course_id: "a/b/c",
                topic_id: "awesomeness",
                date_created: "",
                description: "TeamDescription",
                country: "c",
                language: "a",
                membership: []
            },
            verifyValidation = function (requests, fieldsData) {
                _.each(fieldsData, function (fieldData) {
                    teamEditView.$(fieldData[0]).val(fieldData[1]);
                });

                teamEditView.$('.create-team.form-actions .action-primary').click();

                var message = teamEditView.$('.wrapper-msg');
                expect(message.hasClass('is-hidden')).toBeFalsy();
                expect(message.find('.title').text().trim()).toBe("Your team could not be created!");
                expect(message.find('.copy').text().trim()).toBe(
                    "Check the highlighted fields below and try again."
                );

                _.each(fieldsData, function (fieldData) {
                    if(fieldData[2] === 'error') {
                        expect(teamEditView.$(fieldData[0].split(" ")[0] + '.error').length).toBe(1);
                    } else if(fieldData[2] === 'success') {
                        expect(teamEditView.$(fieldData[0].split(" ")[0] + '.error').length).toBe(0);
                    }
                });

                expect(requests.length).toBe(0);
            },
            expectContent = function (selector, text) {
                expect(teamEditView.$(selector).text().trim()).toBe(text);
            },
            verifyDropdownData = function (selector, expectedItems) {
                var options = teamEditView.$(selector)[0].options;
                var renderedItems = $.map(options, function( elem ) {
                    return [[elem.value, elem.text]];
                });
                for (var i = 0; i < expectedItems.length; i++) {
                    expect(renderedItems).toContain(expectedItems[i]);
                }
            };

        beforeEach(function () {
            setFixtures('<div class="teams-content"></div>');
            spyOn(Backbone.history, 'navigate');
            teamEditView = new TeamEditView({
                el: $('.teams-content'),
                teamParams: {
                    teamsUrl: teamsUrl,
                    courseId: "a/b/c",
                    topicId: 'awesomeness',
                    topicName: 'Awesomeness',
                    languages: [['a', 'aaa'], ['b', 'bbb']],
                    countries: [['c', 'ccc'], ['d', 'ddd']]
                }
            }).render();
        });

        it('can render itself correctly', function () {
            var fieldClasses = [
                '.u-field-name',
                '.u-field-description',
                '.u-field-optional_description',
                '.u-field-language',
                '.u-field-country'
            ];

            _.each(fieldClasses, function (fieldClass) {
                expect(teamEditView.$el.find(fieldClass).length).toBe(1);
            });

            expect(teamEditView.$('.create-team.form-actions .action-primary').length).toBe(1);
            expect(teamEditView.$('.create-team.form-actions .action-cancel').length).toBe(1);
        });

        it('can create a team', function () {
            var requests = AjaxHelpers.requests(this);

            teamEditView.$('.u-field-name input').val(teamsData.name);
            teamEditView.$('.u-field-textarea textarea').val(teamsData.description);
            teamEditView.$('.u-field-language select').val('a').attr("selected", "selected");
            teamEditView.$('.u-field-country select').val('c').attr("selected", "selected");

            teamEditView.$('.create-team.form-actions .action-primary').click();
            AjaxHelpers.expectJsonRequest(requests, 'POST', teamsUrl, teamsData);
            AjaxHelpers.respondWithJson(requests, _.extend(_.extend({}, teamsData), { id: '123'}));

            expect(teamEditView.$('.create-team.wrapper-msg .copy').text().trim().length).toBe(0);
            expect(Backbone.history.navigate.calls[0].args).toContain('teams/awesomeness/123');
        });

        it('shows validation error message when field is empty', function () {
            var requests = AjaxHelpers.requests(this);
            verifyValidation(requests, [
                ['.u-field-name input', 'Name', 'success'],
                ['.u-field-textarea textarea', '', 'error']
            ]);
            teamEditView.render();
            verifyValidation(requests, [
                ['.u-field-name input', '', 'error'],
                ['.u-field-textarea textarea', 'description', 'success']
            ]);
            teamEditView.render();
            verifyValidation(requests, [
                ['.u-field-name input', '', 'error'],
                ['.u-field-textarea textarea', '', 'error']
            ]);
        });

        it('shows validation error message when field value length exceeded the limit', function () {
            var requests = AjaxHelpers.requests(this);
            var teamName = new Array(500 + 1).join( '$' );
            var teamDescription = new Array(500 + 1).join( '$' );

            verifyValidation(requests, [
                ['.u-field-name input', teamName, 'error'],
                ['.u-field-textarea textarea', 'description', 'success']
            ]);
            teamEditView.render();
            verifyValidation(requests, [
                ['.u-field-name input', 'name', 'success'],
                ['.u-field-textarea textarea', teamDescription, 'error']
            ]);
            teamEditView.render();
            verifyValidation(requests, [
                ['.u-field-name input', teamName, 'error'],
                ['.u-field-textarea textarea', teamDescription, 'error']
            ]);
        });

        it("shows an error message for HTTP 500", function () {
            var requests = AjaxHelpers.requests(this);

            teamEditView.$('.u-field-name input').val(teamsData.name);
            teamEditView.$('.u-field-textarea textarea').val(teamsData.description);

            teamEditView.$('.create-team.form-actions .action-primary').click();
            teamsData.country = '';
            teamsData.language = '';
            AjaxHelpers.expectJsonRequest(requests, 'POST', teamsUrl, teamsData);
            AjaxHelpers.respondWithError(requests);

            expect(teamEditView.$('.wrapper-msg .copy').text().trim()).toBe("An error occurred. Please try again.");
        });

        it("changes route on cancel click", function () {
            teamEditView.$('.create-team.form-actions .action-cancel').click();
            expect(Backbone.history.navigate.calls[0].args).toContain('topics/awesomeness');
        });
    });
});
