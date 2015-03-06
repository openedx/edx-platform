var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortDiscussionsView = Backbone.View.extend({

        setDisabled: function($element, enable) {
            if (enable) {
                $element.prop('disabled', false);
            } else {
                $element.prop('disabled', 'disabled');
            }
        },

        getCohortedDiscussions: function(selector) {
            var self=this;

            this.cohortedDiscussions = [];
            _.each(self.$(selector), function (topic) {
                self.cohortedDiscussions.push($(topic).data('id'))
            });
        },

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

        showMessage: function (message, $element, type) {
            var model = new NotificationModel({type: type || 'confirmation', title: message});
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            $element.before(this.notification.$el);
            this.notification.render();
        },

        removeNotification: function () {
            if (this.notification) {
                this.notification.remove();
            }
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView
);
