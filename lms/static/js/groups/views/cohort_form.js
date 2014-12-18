var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text, CohortModel, NotificationModel, NotificationView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortFormView = Backbone.View.extend({
        events : {
            'change .cohort-management-details-association-course input': 'onRadioButtonChange',
            'change .input-cohort-group-association': 'onGroupAssociationChange',
            'click .tab-content-settings .action-save': 'saveSettings',
            'submit .cohort-management-group-add-form': 'addStudents'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-form-tpl').text());
            this.cohortUserPartitionId = options.cohortUserPartitionId;
            this.contentGroups = options.contentGroups;
        },

        showNotification: function(options, beforeElement) {
            var model = new NotificationModel(options);
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            this.notification.render();
            if (!beforeElement) {
                beforeElement = this.$('.cohort-management-group');
            }
            beforeElement.before(this.notification.$el);
        },

        removeNotification: function() {
            if (this.notification) {
                this.notification.remove();
            }
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model,
                contentGroups: this.contentGroups
            }));
            return this;
        },

        onRadioButtonChange: function(event) {
            var target = $(event.currentTarget),
                groupsEnabled = target.val() === 'yes';
            if (!groupsEnabled) {
                // If the user has chosen 'no', then clear the selection by setting
                // it to the first option ('Choose a content group to associate').
                this.$('.input-cohort-group-association').val('None');
            }
        },

        onGroupAssociationChange: function(event) {
            // Since the user has chosen a content group, click the 'Yes' button too
            this.$('.cohort-management-details-association-course .radio-yes').click();
        },

        getSelectedGroupId: function() {
            var selectValue = this.$('.input-cohort-group-association').val();
            if (!this.$('.radio-yes').prop('checked') || selectValue === 'None') {
                return null;
            }
            return parseInt(selectValue);
        },

        getUpdatedCohortName: function() {
            var cohortName = this.$('.cohort-name').val();
            return cohortName ? cohortName.trim() : this.model.get('name');
        },

        saveForm: function() {
            var self = this,
                cohort = this.model,
                saveOperation = $.Deferred(),
                cohortName, groupId, showMessage, showAddError;
            this.removeNotification();
            showMessage = function(message, type) {
                self.showNotification(
                    {type: type || 'confirmation', title: message},
                    self.$('.form-fields')
                );
            };
            showAddError = function(message, type) {
                showMessage(message, 'error');
            };
            cohortName = this.getUpdatedCohortName();
            if (cohortName.length === 0) {
                showAddError(gettext('Please enter a name for your new cohort group.'));
                saveOperation.reject();
            } else {
                groupId = this.getSelectedGroupId();
                cohort.save(
                    {name: cohortName, user_partition_id: this.cohortUserPartitionId, group_id: groupId},
                    {patch: true}
                ).done(function(result) {
                    if (!result.error) {
                        cohort.id = result.id;
                        showMessage(gettext('Saved cohort group.'));
                        saveOperation.resolve();
                    } else {
                        showAddError(result.error);
                        saveOperation.reject();
                    }
                }).fail(function(result) {
                    var errorMessage = null;
                    try {
                        var jsonResponse = JSON.parse(result.responseText);
                        errorMessage = jsonResponse.error;
                    } catch(e) {
                        // Ignore the exception and show the default error message instead.
                    }
                    if (!errorMessage) {
                        errorMessage = gettext("We've encountered an error. Please refresh your browser and then try again.");
                    }
                    showAddError(errorMessage);
                    saveOperation.reject();
                });
            }
            return saveOperation.promise();
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, edx.groups.CohortModel, NotificationModel, NotificationView);
