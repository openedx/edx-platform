var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events: {
            'change .check-discussion-category': 'changeDiscussionCategory',
            'change .check-discussion-subcategory': 'changeDiscussionSubCategory',
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm',
            'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
            'change .check-all-inline-discussions': 'changeAllInlineDiscussions'
        },

        initialize: function () {
            this.template = _.template($('#cohort-discussions-tpl').text());
        },
        render: function () {
            var inlineTopicsHtml = this.renderInlineTopics(this.model),
                coursewideTopicsHtml = this.renderCoursewideTopics(this.model.get('entries'));

            this.$el.html(this.template({
                coursewideTopics: coursewideTopicsHtml,
                inlineTopicsHtml: inlineTopicsHtml
            }));
        },
        renderCoursewideTopics: function (topics) {
            var entry_template = _.template($('#cohort-discussions-subcategory-tpl').html());
            return _.map(topics, function (topic, topic_name) {
                return entry_template({
                    name: topic_name,
                    id: topic.id,
                    is_cohorted: topic.is_cohorted,
                    type: 'coursewide'
                });
            }).join('');
        },
        renderInlineTopics: function (category) {
            var category_template = _.template($('#cohort-discussions-category-tpl').html()),
                entry_template = _.template($('#cohort-discussions-subcategory-tpl').html()),
                children = category.children || category.get('children');

            return _.map(children, function (name) {
                var html = '', entry,
                    entries = category.entries || category.get('entries'),
                    subcategories = category.subcategories || category.get('subcategories');

                if (_.has(entries, name)) {
                    entry = entries[name];
                    html = entry_template({
                        name: name,
                        id: entry.id,
                        is_cohorted: entry.is_cohorted,
                        type: 'inline'
                    });
                } else { // subcategory
                    html = category_template({
                        name: name,
                        entries: this.renderInlineTopics(subcategories[name])
                    });
                }
                return html;
            }, this).join('');
        },
        //toggleSaveButton: function(event) {
        //    $('.cohort-coursewide-discussions-form .action-save').prop('disabled', '');
        //    $('.cohort-coursewide-discussions-form .action-save').off('click');
        //},
        changeDiscussionCategory: function(event) {
            event.preventDefault();
            var $selectedCategory = $(event.currentTarget),
                $parentCategory = $selectedCategory.parent('li'),
                $childCategoires = $parentCategory.find('.check-discussion-category'),
                $childSubCategoires = $parentCategory.find('.check-discussion-subcategory-inline');

            if ($selectedCategory.prop('checked')) {
                $childCategoires.prop('checked', 'checked');
                $childSubCategoires.prop('checked', 'checked');
            } else {
                $childCategoires.prop('checked', false);
                $childSubCategoires.prop('checked', false);
            }
        },
        changeDiscussionSubCategory: function (event) {
            event.preventDefault();
            var $selectedTopic = $(event.currentTarget),
                isTopicChecked = $selectedTopic.prop('checked'),
                id = $selectedTopic.data('id'),
                currentModel = this.model.get('entries').get(id);
            currentModel.set({'is_cohorted': isTopicChecked});
        },

        getCohortedDiscussions: function(selector) {
            var self=this;
            self.cohortedDiscussionTopics = [];
            _.each(self.$(selector), function (topic) {
                self.cohortedDiscussionTopics.push($(topic).data('id'))
            });
        },
        saveInlineDiscussionsForm: function (event) {
            var self = this,
                fieldData;
            event.preventDefault();

            self.getCohortedDiscussions('.check-discussion-subcategory-inline:checked');
            fieldData = {
                inline_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };
            self.removeNotification();
            self.saveForm(fieldData)
                .done(function () {
                    self.model.fetch().done(function () {
                        self.showMessage(
                            gettext('The discussion topic(s) has been cohorted.'),
                            self.$('.coursewide-discussion-topics')
                        );
                    });
                });
        },
        saveCoursewideDiscussionsForm: function (event) {
            var self = this,
                fieldData;
            event.preventDefault();

            self.getCohortedDiscussions('.check-discussion-topic-coursewide:checked');
            fieldData = {
                coursewide_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };
            self.removeNotification();
            self.saveForm(fieldData)
                .done(function () {
                    self.model.fetch().done(function () {
                        self.showMessage(
                            gettext('The discussion topic(s) has been cohorted.'),
                            self.$('.coursewide-discussion-topics')
                        );
                    });
                });
        },
        saveForm: function (fieldData) {
            var self = this,
                discussionsModel = this.model,
                saveOperation = $.Deferred(),
                showErrorMessage;
            showErrorMessage = function (message) {
                self.showMessage(message, self.$('.coursewide-discussion-topics'), 'error');
            };
            this.removeNotification();

            discussionsModel.save(
                fieldData, {wait: true}
            ).done(function (result) {
                    self.render();    // re-render to remove any now invalid error messages
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
                    showErrorMessage(errorMessage);
                    saveOperation.reject();
                });
            return saveOperation.promise();
        },

        showMessage: function (message, element, type) {
            this.showNotification(
                {type: type || 'confirmation', title: message},
                element
            );
        },
        showNotification: function (options, beforeElement) {
            var model = new NotificationModel(options);
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            beforeElement.before(this.notification.$el);
            this.notification.render();
        },
        removeNotification: function () {
            if (this.notification) {
                this.notification.remove();
            }
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView);
