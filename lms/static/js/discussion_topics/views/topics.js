var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text, DiscussionTopicItemView) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events : {
            'change .discussion-topic': 'toggleTopicCheck',
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            this.context = options.context;
            this.model.get('entries').on("change", this.render, this);
            this.cohortedDiscussionTopics = [];
        },
        render: function() {
            this.$el.html(this.template({
                coursewideTopics: this.model.get('entries').models,
                inlineTopics: this.model.get('subcategories')
            }));

            //var topicsList = this.model.get('entries'),
            //    self = this;
            //topicsList.each(function(topic) {
            //    var topicItem = new DiscussionTopicItemView({ model: topic });
            //    self.$el.append(topicItem.render().el);
            //});
        },
        toggleSaveButton: function(event) {
            $('.cohort-coursewide-discussions-form .action-save').prop('disabled', '');
            $('.cohort-coursewide-discussions-form .action-save').off('click');
        },

        toggleTopicCheck: function (event) {
            event.preventDefault();

            var $selectedTopic = $(event.currentTarget),
                isTopicChecked = $selectedTopic.prop('checked'),
                id = $selectedTopic.data('id');

            //isTopicChecked ? this.cohortedDiscussionTopics.push(id): this.cohortedDiscussionTopics;
            var currentModel = this.model.get('entries').get(id);
            currentModel.set({'is_cohorted': isTopicChecked});
        },

        saveCoursewideDiscussionsForm: function(event) {
            var self = this,
                cohortedTopics=this.$('.check-discussion-topic:checked');
            _.each(cohortedTopics, function(topic){
                self.cohortedDiscussionTopics.push($(topic).data('id'))
            });
            event.preventDefault();
            //this.removeNotification();
            this.saveForm()
                .done(function() {
                    self.model.fetch().done(function() {
                        self.showNotification({
                            type: 'confirmation',
                            title: interpolate_text(
                                gettext('The cohort has been created. You can manually add students to this cohort below.')
                            )
                        });
                    });
                });
        },
        saveForm: function() {
            var self = this,
                coursewideDiscussions = this.model,
                saveOperation = $.Deferred(),
                //isUpdate = !_.isUndefined(this.model.id),
                fieldData, errorMessages, showErrorMessage;
            //showErrorMessage = function(message, details) {
            //    self.showMessage(message, 'error', details);
            //};
            //this.removeNotification();
            fieldData = {
                coursewide_discussions: this.cohortedDiscussionTopics
            };
            //errorMessages = this.validate(fieldData);

            //if (errorMessages.length > 0) {
            //    showErrorMessage(
            //        isUpdate ? gettext("The cohort cannot be saved") : gettext("The cohort cannot be added"),
            //        errorMessages
            //    );
            //    saveOperation.reject();
            //} else {
            coursewideDiscussions.save(
                fieldData, {wait: true, patch:true}
            ).done(function(result) {
                //cohort.id = result.id;
                //self.render();    // re-render to remove any now invalid error messages
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
            //}
            return saveOperation.promise();
        },
        getCohortedTopics: function(){
            var self=this,
                cohortedTopics=this.$('.check-discussion-topic:checked');
            _.each(cohortedTopics, function(topic){
                self.cohortedDiscussionTopics.push(topic.data('id'));
            });
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, edx.discussions.DiscussionTopicItemView);
