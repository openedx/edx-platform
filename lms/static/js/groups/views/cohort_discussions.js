var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortDiscussionConfigurationView = Backbone.View.extend({

        /**
         * Add/Remove the disabled attribute on given element.
         * @param {object} $element - The element to disable/enable.
         * @param {bool} disable - The flag to add/remove 'disabled' attribute.
         */
        setDisabled: function($element, disable) {
            $element.prop('disabled', disable ? 'disabled' : false);
        },

        /**
         * Returns the cohorted discussions list.
         * @param {string} selector - To select the discussion elements whose ids to return.
         * @returns {Array} - Cohorted discussions.
         */
        getCohortedDiscussions: function(selector) {
            var self=this,
                cohortedDiscussions = [];

            _.each(self.$(selector), function (topic) {
                cohortedDiscussions.push($(topic).data('id'))
            });
            return cohortedDiscussions;
        },

        /**
         * Save the cohortSettings' changed attributes to the server via PATCH method.
         * It shows the error message(s) if any.
         * @param {object} $element - Messages would be shown before this element.
         * @param {object} fieldData - Data to update on the server.
         */
        saveForm: function ($element, fieldData) {
            var self = this,
                cohortSettingsModel = this.cohortSettings,
                saveOperation = $.Deferred(),
                showErrorMessage;

            showErrorMessage = function (message, $element) {
                self.showMessage(message, $element, 'error');
            };
            this.removeNotification();

            cohortSettingsModel.save(
                fieldData, {patch: true, wait: true}
            ).done(function () {
                saveOperation.resolve();
            }).fail(function (result) {
                var errorMessage = null;
                try {
                    var jsonResponse = JSON.parse(result.responseText);
                    errorMessage = jsonResponse.error;
                } catch (e) {
                    // Ignore the exception and show the default error message instead.
                }
                if (!errorMessage) {
                    errorMessage = gettext("We've encountered an error. Refresh your browser and then try again.");
                }
                showErrorMessage(errorMessage, $element);
                saveOperation.reject();
            });
            return saveOperation.promise();
        },

        /**
         * Shows the notification messages before given element using the NotificationModel.
         * @param {string} message - Text message to show.
         * @param {object} $element - Message would be shown before this element.
         * @param {string} type - Type of message to show e.g. confirmation or error.
         */
        showMessage: function (message, $element, type) {
            var model = new NotificationModel({type: type || 'confirmation', title: message});
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            $element.before(this.notification.$el);
            this.notification.render();
        },

        /**
         *Removes the notification messages.
         */
        removeNotification: function () {
            if (this.notification) {
                this.notification.remove();
            }
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView
);
