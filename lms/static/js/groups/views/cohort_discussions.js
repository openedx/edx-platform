var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortDiscussionsView = Backbone.View.extend({

        /**
        Add/Remove the disabled attribute on given element.

        Args:
            $element (JQuery element): The element to disable/enable.
            disable (Bool): The flag to add/remove 'disabled' attribute.
        **/
        setDisabled: function($element, disable) {
            if (disable) {
                $element.prop('disabled', 'disabled');
            } else {
                $element.prop('disabled', false);
            }
        },

        /**
        Returns the cohorted discussions list.

        Args:
            selector (HTML element): The topic element to get the ids.

        Returns:
            Cohorted discussions list.
        **/
        getCohortedDiscussions: function(selector) {
            var self=this,
                cohortedDiscussions = [];

            _.each(self.$(selector), function (topic) {
                cohortedDiscussions.push($(topic).data('id'))
            });

            return cohortedDiscussions;
        },

        /**
        Save the cohortSettings' changed attributes to the server via PATCH method.
         Also, it shows the error message(s) if any.

        Args:
            $element (JQuery element): Messages would be shown before this element.
        **/
        saveForm: function ($element) {
            var self = this,
                cohortSettingsModel = this.cohortSettings,
                saveOperation = $.Deferred(),
                showErrorMessage;

            showErrorMessage = function (message, $element) {
                self.showMessage(message, $element, 'error');
            };
            this.removeNotification();

            cohortSettingsModel.save(
                cohortSettingsModel.changedAttributes(), {patch: true, wait: true}
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
        Shows the notification messages before given element using the NotificationModel.

        Args:
            message (string): Text message to show.
            $element (JQuery element): Message would be shown before this element.
            type (string): Type of message to show e.g. confirmation or error.
        **/
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
        Removes the notification messages.
        **/
        removeNotification: function () {
            if (this.notification) {
                this.notification.remove();
            }
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView
);
