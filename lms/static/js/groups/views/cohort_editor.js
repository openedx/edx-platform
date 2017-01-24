(function(define) {
    'use strict';
    define(['backbone', 'underscore', 'jquery', 'gettext', 'js/groups/views/cohort_form', 'string_utils',
            'js/models/notification', 'js/views/notification'],
        function(Backbone, _, $, gettext, CohortFormView) {
            var CohortEditorView = Backbone.View.extend({

                events: {
                    'click .wrapper-tabs .tab': 'selectTab',
                    'click .tab-content-settings .action-save': 'saveSettings',
                    'click .tab-content-settings .action-cancel': 'cancelSettings',
                    'submit .cohort-management-group-add-form': 'addStudents'
                },

                initialize: function(options) {
                    this.template = _.template($('#cohort-editor-tpl').text());
                    this.groupHeaderTemplate = _.template($('#cohort-group-header-tpl').text());
                    this.cohorts = options.cohorts;
                    this.contentGroups = options.contentGroups;
                    this.context = options.context;
                },

                // Any errors that are currently being displayed to the instructor (for example, unknown email addresses).
                errorNotifications: null,
                // Any confirmation messages that are currently being displayed (for example, number of students added).
                confirmationNotifications: null,

                render: function() {
                    this.$el.html(this.template({
                        cohort: this.model
                    }));
                    this.renderGroupHeader();
                    this.cohortFormView = new CohortFormView({
                        model: this.model,
                        contentGroups: this.contentGroups,
                        context: this.context
                    });
                    this.cohortFormView.render();
                    this.$('.tab-content-settings').append(this.cohortFormView.$el);
                    return this;
                },

                renderGroupHeader: function() {
                    this.$('.cohort-management-group-header').html(this.groupHeaderTemplate({
                        cohort: this.model
                    }));
                },

                selectTab: function(event) {
                    var tabElement = $(event.currentTarget),
                        tabName = tabElement.data('tab');
                    event.preventDefault();
                    this.$('.wrapper-tabs .tab').removeClass('is-selected');
                    this.$('.wrapper-tabs .tab').find('span.sr').remove();
                    tabElement.addClass('is-selected');
                    tabElement.find('a').prepend('<span class="sr">' + gettext('Selected tab') + ' </span>');
                    this.$('.tab-content').addClass('is-hidden');
                    this.$('.tab-content-' + tabName).removeClass('is-hidden').focus();
                },

                saveSettings: function(event) {
                    var cohortFormView = this.cohortFormView;
                    var self = this;
                    event.preventDefault();
                    cohortFormView.saveForm()
                        .done(function() {
                            self.renderGroupHeader();
                            cohortFormView.showMessage(gettext('Saved cohort'));
                        });
                },

                cancelSettings: function(event) {
                    event.preventDefault();
                    this.render();
                },

                setCohort: function(cohort) {
                    this.model = cohort;
                    this.render();
                },

                addStudents: function(event) {
                    event.preventDefault();
                    var self = this,
                        cohorts = this.cohorts,
                        input = this.$('.cohort-management-group-add-students'),
                        add_url = this.model.url() + '/add',
                        students = input.val().trim(),
                        cohortId = this.model.id;

                    if (students.length > 0) {
                        $.post(
                            add_url, {'users': students}
                        ).done(function(modifiedUsers) {
                            self.refreshCohorts().done(function() {
                                // Find the equivalent cohort in the new collection and select it
                                var cohort = cohorts.get(cohortId);
                                self.setCohort(cohort);

                                // Show the notifications
                                self.addNotifications(modifiedUsers);

                                // If an unknown user was specified then update the new input to have
                                // the original input's value. This is to allow the user to correct the
                                // value in case it was a typo.
                                if (modifiedUsers.unknown.length > 0) {
                                    self.$('.cohort-management-group-add-students').val(students);
                                }
                            });
                        }).fail(function() {
                            self.showErrorMessage(gettext('Error adding students.'), true);
                        });
                    } else {
                        self.showErrorMessage(gettext('Enter a username or email.'), true);
                        input.val('');
                    }
                },

                /**
                * Refresh the cohort collection to get the latest set as well as up-to-date counts.
                */
                refreshCohorts: function() {
                    return this.cohorts.fetch();
                },

                undelegateViewEvents: function(view) {
                    if (view) {
                        view.undelegateEvents();
                    }
                },

                showErrorMessage: function(message, removeConfirmations, model) {
                    if (removeConfirmations && this.confirmationNotifications) {
                        this.undelegateViewEvents(this.confirmationNotifications);
                        this.confirmationNotifications.$el.html('');
                        this.confirmationNotifications = null;
                    }
                    if (model === undefined) {
                        model = new NotificationModel();
                    }
                    model.set('type', 'error');
                    model.set('title', message);

                    this.undelegateViewEvents(this.errorNotifications);

                    this.errorNotifications = new NotificationView({
                        el: this.$('.cohort-errors'),
                        model: model
                    });
                    this.errorNotifications.render();
                },

                addNotifications: function(modifiedUsers) {
                    var oldCohort, title, details, numPresent, numUsersAdded, numErrors,
                        createErrorDetails, errorActionCallback, errorModel,
                        errorLimit = 5;

                    // Show confirmation messages.
                    this.undelegateViewEvents(this.confirmationNotifications);
                    numUsersAdded = modifiedUsers.added.length + modifiedUsers.changed.length;
                    numPresent = modifiedUsers.present.length;
                    if (numUsersAdded > 0 || numPresent > 0) {
                        title = interpolate_text(
                            ngettext('{numUsersAdded} student has been added to this cohort',
                                '{numUsersAdded} students have been added to this cohort', numUsersAdded),
                            {numUsersAdded: numUsersAdded}
                        );

                        var movedByCohort = {};
                        _.each(modifiedUsers.changed, function(changedInfo) {
                            oldCohort = changedInfo.previous_cohort;
                            if (oldCohort in movedByCohort) {
                                movedByCohort[oldCohort] = movedByCohort[oldCohort] + 1;
                            }
                            else {
                                movedByCohort[oldCohort] = 1;
                            }
                        });

                        details = [];
                        for (oldCohort in movedByCohort) {
                            details.push(
                                interpolate_text(
                                    ngettext('{numMoved} student was removed from {oldCohort}',
                                        '{numMoved} students were removed from {oldCohort}', movedByCohort[oldCohort]),
                                    {numMoved: movedByCohort[oldCohort], oldCohort: oldCohort}
                                )
                            );
                        }
                        if (numPresent > 0) {
                            details.push(
                                interpolate_text(
                                    ngettext('{numPresent} student was already in the cohort',
                                        '{numPresent} students were already in the cohort', numPresent),
                                    {numPresent: numPresent}
                                )
                            );
                        }

                        this.confirmationNotifications = new NotificationView({
                            el: this.$('.cohort-confirmations'),
                            model: new NotificationModel({
                                type: 'confirmation',
                                title: title,
                                details: details
                            })
                        });
                        this.confirmationNotifications.render();
                    }
                    else if (this.confirmationNotifications) {
                        this.confirmationNotifications.$el.html('');
                        this.confirmationNotifications = null;
                    }

                    // Show error messages.
                    this.undelegateViewEvents(this.errorNotifications);
                    numErrors = modifiedUsers.unknown.length;
                    if (numErrors > 0) {
                        createErrorDetails = function(unknownUsers, showAllErrors) {
                            var numErrors = unknownUsers.length, details = [];

                            for (var i = 0; i < (showAllErrors ? numErrors : Math.min(errorLimit, numErrors)); i++) {
                                details.push(interpolate_text(gettext('Unknown user: {user}'), {user: unknownUsers[i]}));
                            }
                            return details;
                        };

                        title = interpolate_text(
                            ngettext('There was an error when trying to add students:',
                                'There were {numErrors} errors when trying to add students:', numErrors),
                            {numErrors: numErrors}
                        );
                        details = createErrorDetails(modifiedUsers.unknown, false);

                        errorActionCallback = function(view) {
                            view.model.set('actionText', null);
                            view.model.set('details', createErrorDetails(modifiedUsers.unknown, true));
                            view.render();
                        };

                        errorModel = new NotificationModel({
                            details: details,
                            actionText: numErrors > errorLimit ? gettext('View all errors') : null,
                            actionCallback: errorActionCallback,
                            actionClass: 'action-expand'
                        });

                        this.showErrorMessage(title, false, errorModel);
                    }
                    else if (this.errorNotifications) {
                        this.errorNotifications.$el.html('');
                        this.errorNotifications = null;
                    }
                }
            });
            return CohortEditorView;
        });
}).call(this, define || RequireJS.define);
