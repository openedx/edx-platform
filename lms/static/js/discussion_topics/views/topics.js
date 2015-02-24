var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events : {
            'change .check-discussion-topic': 'toggleTopicCheck',
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-topics-tpl').text());
            this.context = options.context;
            this.model.get('entries').on("change", this.render, this);
            this.cohortedDiscussionTopics = [];
        },
        render: function() {
            this.$el.html(this.template({
                coursewideTopics: this.model.get('entries').models,
                inlineTopics: this.model.get('subcategories')
            }));
        },
        toggleSaveButton: function(event) {
            $('.cohort-coursewide-discussions-form .action-save').prop('disabled', '');
            $('.cohort-coursewide-discussions-form .action-save').off('click');
        },

        toggleTopicCheck: function (event) {
            event.preventDefault();

            var $selectedTopic = $(event.currentTarget),
                isTopicChecked = $selectedTopic.prop('checked'),
                id = $selectedTopic.data('id'),
                currentModel = this.model.get('entries').get(id);
            currentModel.set({'is_cohorted': isTopicChecked});
        },

        saveCoursewideDiscussionsForm: function(event) {
            var self = this;
            event.preventDefault();

            this.removeNotification();
            this.saveForm()
                .done(function() {
                    self.model.fetch().done(function() {
                        self.showMessage(
                            gettext('The discussion topic(s) has been cohorted.'),
                            self.$('.coursewide-discussion-topics')
                        );
                    });
                });
        },
        saveForm: function() {
            var self = this,
                coursewideDiscussions = this.model,
                saveOperation = $.Deferred(),
                fieldData, errorMessages, showErrorMessage;
            showErrorMessage = function(message) {
                self.showMessage(message, self.$('.coursewide-discussion-topics'), 'error');
            };
            this.removeNotification();
            fieldData = {
                coursewide_discussions: true
            };

            coursewideDiscussions.save(
                fieldData, {wait: true}
            ).done(function(result) {
                //cohort.id = result.id;
                self.render();    // re-render to remove any now invalid error messages
                saveOperation.resolve();
            }).fail(function(result) {
                var errorMessage = null;
                try {
                    var jsonResponse = JSON.parse(result.responseText);
                    errorMessage = jsonResponse.error;
                } catch(e) {
                    // Ignore the exception and show the default error message instead.
                }
                if (!errorMessage) {
                    errorMessage = gettext("We've encountered an error. Refresh your browser and then try again.");
                }
                showErrorMessage(errorMessage);
                saveOperation.reject();
            });
            return saveOperation.promise();
        },

        showMessage: function(message, element, type) {
            this.showNotification(
                {type: type || 'confirmation', title: message},
                element
            );
        },
        showNotification: function(options, beforeElement) {
            var model = new NotificationModel(options);
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            beforeElement.before(this.notification.$el);
            this.notification.render();
        },
        removeNotification: function() {
            if (this.notification) {
                this.notification.remove();
            }
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView);
