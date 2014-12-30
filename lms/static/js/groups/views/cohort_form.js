var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text, CohortModel, NotificationModel, NotificationView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortFormView = Backbone.View.extend({
        events : {
            'change .field-radio input': 'onRadioButtonChange',
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
            this.$('.input-cohort-group-association').toggleClass('is-disabled', !groupsEnabled);
        },

        getSelectedGroupId: function() {
            if (!this.$('.radio-yes').prop('checked')) {
                return null;
            }
            return parseInt(this.$('.input-cohort-group-association').val());
        },

        getUpdatedCohortName: function() {
            var cohortName = this.$('.cohort-name').val();
            return cohortName ? cohortName.trim() : this.model.get('name');
        },

        saveForm: function() {
            var self = this,
                cohort = this.model,
                saveOperation = $.Deferred(),
                cohortName, groupId, showAddError;
            this.removeNotification();
            showAddError = function(message) {
                self.showNotification(
                    {type: 'error', title: message},
                    self.$('.form-fields')
                );
            };
            cohortName = this.getUpdatedCohortName();
            if (cohortName.length === 0) {
                showAddError(gettext('Please enter a name for your new cohort group.'));
                saveOperation.reject();
            } else {
                groupId = this.getSelectedGroupId();
                cohort.save(
                    {name: cohortName, user_partition_id: this.cohortUserPartitionId, group_id: groupId}
                ).done(function(result) {
                    if (!result.error) {
                        cohort.id = result.id;
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
