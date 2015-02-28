var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events: {
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm',
            'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
            'change .check-all-inline-discussions': 'changeAllInlineDiscussions'
        },

        initialize: function () {
            this.template = _.template($('#cohort-discussions-tpl').text());
        },
        render: function () {
            this.$el.html(this.template({
                coursewideTopics: this.renderCoursewideTopics(this.model.get('coursewide_categories')),
                inlineTopicsHtml: this.renderInlineTopics(this.model),
                always_cohort_inline_discussions:this.model.get('always_cohort_inline_discussions')
            }));
            $('ul.inline-cohorts').qubit();
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
                is_category_cohorted = true,
                children = category.children || category.get('children');

            return _.map(children, function (name) {
                var html = '', entry,
                    entries = category.entries || category.get('entries'),
                    subcategories = category.subcategories || category.get('subcategories');


                var filteredEntry = _.find(entries,function(entry){
                    if (entry.is_cohorted === false) {
                        // breaks the loop and returns the current entry.
                        return true;
                    }
                });
                if (filteredEntry) {
                    is_category_cohorted = false;
                }

                if (entries && _.has(entries, name)) {
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
                        entries: this.renderInlineTopics(subcategories[name]),
                        is_category_cohorted: is_category_cohorted
                    });
                }
                return html;
            }, this).join('');
        },
        //toggleSaveButton: function(event) {
        //    $('.cohort-coursewide-discussions-form .action-save').prop('disabled', '');
        //    $('.cohort-coursewide-discussions-form .action-save').off('click');
        //},

        getCohortedDiscussions: function(selector) {
            var self=this;
            self.cohortedDiscussionTopics = [];
            _.each(self.$(selector), function (topic) {
                self.cohortedDiscussionTopics.push($(topic).data('id'))
            });
        },
        saveInlineDiscussionsForm: function (event) {
            event.preventDefault();
            var self = this,
                fieldData,
                $inlineTopics = self.$('.inline-discussion-topics');

            self.getCohortedDiscussions('.check-discussion-subcategory-inline:checked');
            fieldData = {
                inline_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics,
                always_cohort_inline_discussions:self.$('.check-all-inline-discussions').prop('checked')
            };
            self.saveForm(fieldData, $inlineTopics)
                .done(function () {
                    self.model.fetch().done(function () {
                        self.showMessage(gettext('Changes Saved.'), $inlineTopics);
                    });
                });
        },
        saveCoursewideDiscussionsForm: function (event) {
            var self = this,
                fieldData,
                $coursewideTopics = self.$('.coursewide-discussion-topics');
            event.preventDefault();
            self.getCohortedDiscussions('.check-discussion-subcategory-coursewide:checked');
            fieldData = {
                coursewide_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };

            self.saveForm(fieldData, $coursewideTopics)
                .done(function () {
                    self.model.fetch().done(function () {
                        self.showMessage(gettext('Changes Saved.'), $coursewideTopics);
                    });
                });
        },
        saveForm: function (fieldData, $element) {
            var self = this,
                discussionsModel = this.model,
                saveOperation = $.Deferred(),
                showErrorMessage;

            showErrorMessage = function (message, $element) {
                self.showMessage(message, $element, 'error');
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
                    showErrorMessage(errorMessage, $element);
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
        showNotification: function (options, $beforeElement) {
            var model = new NotificationModel(options);
            this.removeNotification();
            this.notification = new NotificationView({
                model: model
            });
            $beforeElement.before(this.notification.$el);
            this.notification.render();
        },
        removeNotification: function () {
            if (this.notification) {
                this.notification.remove();
            }
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView);
