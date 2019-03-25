(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext', 'js/models/notification', 'js/views/notification'],
        function($, _, Backbone, gettext) {
            /* global NotificationModel, NotificationView */
            var DividedDiscussionConfigurationView = Backbone.View.extend({

                /**
                * Add/Remove the disabled attribute on given element.
                * @param {object} $element - The element to disable/enable.
                * @param {bool} disable - The flag to add/remove 'disabled' attribute.
                */
                setDisabled: function($element, disable) {
                    $element.prop('disabled', disable ? 'disabled' : false);
                },

                /**
                * Returns the divided discussions list.
                * @param {string} selector - To select the discussion elements whose ids to return.
                * @returns {Array} - Divided discussions.
                */
                getDividedDiscussions: function(selector) {
                    var self = this,
                        dividedDiscussions = [];

                    _.each(self.$(selector), function(topic) {
                        dividedDiscussions.push($(topic).data('id'));
                    });
                    return dividedDiscussions;
                },

                /**
                * Save the discussionSettings' changed attributes to the server via PATCH method.
                * It shows the error message(s) if any.
                * @param {object} $element - Messages would be shown before this element.
                * @param {object} fieldData - Data to update on the server.
                */
                saveForm: function($element, fieldData) {
                    var self = this,
                        discussionSettingsModel = this.discussionSettings,
                        saveOperation = $.Deferred(),
                        showErrorMessage;
                    showErrorMessage = function(message) {
                        self.showMessage(message, $element, 'error');
                    };
                    this.removeNotification();

                    discussionSettingsModel.save(
                        fieldData, {patch: true, wait: true}
                    ).done(function() {
                        saveOperation.resolve();
                    }).fail(function(result) {
                        var errorMessage = null,
                            jsonResponse;
                        try {
                            jsonResponse = JSON.parse(result.responseText);
                            errorMessage = jsonResponse.error;
                        } catch (e) {
                            // Ignore the exception and show the default error message instead.
                        }
                        if (!errorMessage) {
                            errorMessage = gettext("We've encountered an error. Refresh your browser and then try again."); // eslint-disable-line max-len
                        }
                        showErrorMessage(errorMessage);
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
                showMessage: function(message, $element, type) {
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
                removeNotification: function() {
                    if (this.notification) {
                        this.notification.remove();
                    }
                }

            });
            return DividedDiscussionConfigurationView;
        });
}).call(this, define || RequireJS.define);
