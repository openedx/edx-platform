(function(define) {
    'use strict';

    define(['backbone',
        'underscore',
        'gettext',
        'js/views/fields',
        'teams/js/models/team',
        'common/js/components/utils/view_utils',
        'text!teams/templates/edit-team.underscore',
        'edx-ui-toolkit/js/utils/html-utils'],
    function(Backbone, _, gettext, FieldViews, TeamModel, ViewUtils, editTeamTemplate, HtmlUtils) {
        return Backbone.View.extend({

            maxTeamNameLength: 255,
            maxTeamDescriptionLength: 300,

            events: {
                'click .action-primary': ViewUtils.withDisabledElement('createOrUpdateTeam'),
                'submit form': ViewUtils.withDisabledElement('createOrUpdateTeam'),
                'click .action-cancel': 'cancelAndGoBack'
            },

            initialize: function(options) {
                this.teamEvents = options.teamEvents;
                this.context = options.context;
                this.topic = options.topic;
                this.collection = options.collection;
                this.action = options.action;

                if (this.action === 'create') {
                    this.teamModel = new TeamModel({});
                    this.teamModel.url = this.context.teamsUrl;
                    this.primaryButtonTitle = gettext('Create');
                } else if (this.action === 'edit') {
                    this.teamModel = options.model;
                    this.teamModel.url = this.context.teamsDetailUrl.replace('team_id', options.model.get('id')) +
                            '?expand=user';
                    this.primaryButtonTitle = gettext('Update');
                }

                this.teamNameField = new FieldViews.TextFieldView({
                    model: this.teamModel,
                    title: gettext('Team Name (Required) *'),
                    valueAttribute: 'name',
                    helpMessage: gettext('A name that identifies your team (maximum 255 characters).')
                });

                this.teamDescriptionField = new FieldViews.TextareaFieldView({
                    model: this.teamModel,
                    title: gettext('Team Description (Required) *'),
                    valueAttribute: 'description',
                    editable: 'always',
                    showMessages: false,
                    helpMessage: gettext(
                        'A short description of the team to help other learners understand the ' +
                          'goals or direction of the team (maximum 300 characters).')
                });

                this.teamLanguageField = new FieldViews.DropdownFieldView({
                    model: this.teamModel,
                    title: gettext('Language'),
                    valueAttribute: 'language',
                    required: false,
                    showMessages: false,
                    titleIconName: 'fa-comment-o',
                    options: this.context.languages,
                    helpMessage:
                            gettext('The language that team members primarily use to communicate with each other.')
                });

                this.teamCountryField = new FieldViews.DropdownFieldView({
                    model: this.teamModel,
                    title: gettext('Country'),
                    valueAttribute: 'country',
                    required: false,
                    showMessages: false,
                    titleIconName: 'fa-globe',
                    options: this.context.countries,
                    helpMessage: gettext('The country that team members primarily identify with.')
                });
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.template(editTeamTemplate)({
                        primaryButtonTitle: this.primaryButtonTitle,
                        action: this.action,
                        totalMembers: _.isUndefined(this.teamModel) ? 0 : this.teamModel.get('membership').length
                    })
                );
                this.set(this.teamNameField, '.team-required-fields');
                this.set(this.teamDescriptionField, '.team-required-fields');
                this.set(this.teamLanguageField, '.team-optional-fields');
                this.set(this.teamCountryField, '.team-optional-fields');
                return this;
            },

            set: function(view, selector) {
                var viewEl = view.$el;
                if (this.$(selector).has(viewEl).length) {
                    view.render().setElement(viewEl);
                } else {
                    this.$(selector).append(view.render().$el);
                }
            },

            createOrUpdateTeam: function(event) {
                event.preventDefault();
                var view = this, // eslint-disable-line vars-on-top
                    teamLanguage = this.teamLanguageField.fieldValue(),
                    teamCountry = this.teamCountryField.fieldValue(),
                    data = {
                        name: this.teamNameField.fieldValue(),
                        description: this.teamDescriptionField.fieldValue(),
                        language: _.isNull(teamLanguage) ? '' : teamLanguage,
                        country: _.isNull(teamCountry) ? '' : teamCountry
                    },
                    saveOptions = {
                        wait: true
                    };

                if (this.action === 'create') {
                    data.course_id = this.context.courseID;
                    data.topic_id = this.topic.id;
                } else if (this.action === 'edit') {
                    saveOptions.patch = true;
                    saveOptions.contentType = 'application/merge-patch+json';
                }

                var validationResult = this.validateTeamData(data); // eslint-disable-line vars-on-top
                if (validationResult.status === false) {
                    this.showMessage(validationResult.message, validationResult.srMessage);
                    return $().promise();
                }
                return view.teamModel.save(data, saveOptions)
                    .done(function(result) {
                        view.teamEvents.trigger('teams:update', {
                            action: view.action,
                            team: result
                        });
                        Backbone.history.navigate(
                            'teams/' + view.topic.id + '/' + view.teamModel.id,
                            {trigger: true}
                        );
                    })
                    .fail(function(data) { // eslint-disable-line no-shadow
                        var response = JSON.parse(data.responseText);
                        var message = gettext('An error occurred. Please try again.');
                        if ('user_message' in response) {
                            message = response.user_message;
                        }
                        view.showMessage(message, message);
                    });
            },

            validateTeamData: function(data) {
                var status = true,
                    message = gettext('Check the highlighted fields below and try again.');
                var srMessages = [];

                this.teamNameField.unhighlightField();
                this.teamDescriptionField.unhighlightField();

                if (_.isEmpty(data.name.trim())) {
                    status = false;
                    this.teamNameField.highlightFieldOnError();
                    srMessages.push(
                        gettext('Enter team name.')
                    );
                } else if (data.name.length > this.maxTeamNameLength) {
                    status = false;
                    this.teamNameField.highlightFieldOnError();
                    srMessages.push(
                        gettext('Team name cannot have more than 255 characters.')
                    );
                }

                if (_.isEmpty(data.description.trim())) {
                    status = false;
                    this.teamDescriptionField.highlightFieldOnError();
                    srMessages.push(
                        gettext('Enter team description.')
                    );
                } else if (data.description.length > this.maxTeamDescriptionLength) {
                    status = false;
                    this.teamDescriptionField.highlightFieldOnError();
                    srMessages.push(
                        gettext('Team description cannot have more than 300 characters.')
                    );
                }

                return {
                    status: status,
                    message: message,
                    srMessage: srMessages.join(' ')
                };
            },

            showMessage: function(message, screenReaderMessage) {
                this.$('.wrapper-msg').removeClass('is-hidden');
                this.$('.msg-content .copy p').text(message);
                this.$('.wrapper-msg').focus();

                if (screenReaderMessage) {
                    this.$('.screen-reader-message').text(screenReaderMessage);
                }
            },

            cancelAndGoBack: function(event) {
                var url;
                event.preventDefault();
                if (this.action === 'create') {
                    url = 'topics/' + this.topic.id;
                } else if (this.action === 'edit') {
                    url = 'teams/' + this.topic.id + '/' + this.teamModel.get('id');
                }
                Backbone.history.navigate(url, {trigger: true});
            }
        });
    });
}).call(this, define || RequireJS.define);
