var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    var disabledClass = 'is-disabled';
    edx.groups = edx.groups || {};

    edx.groups.DiscussionTopicsView = Backbone.View.extend({
        events: {
            'change .check-discussion-category': 'changeDiscussionInlineCategory',
            'change .check-discussion-subcategory-inline': 'changeDiscussionInlineSubCategory',
            'change .check-discussion-subcategory-coursewide': 'changeDiscussionCoursewideCategory',
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm',
            'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
            'change .check-all-inline-discussions': 'changeAllInlineDiscussions'
        },

        initialize: function () {
            this.template = _.template($('#cohort-discussions-tpl').text());
            this.subCategoryTemplate = _.template($('#cohort-discussions-subcategory-tpl').html());
        },
        render: function () {
            var alwaysCohortInlineDiscussions = this.model.get('always_cohort_inline_discussions');
            this.$el.html(this.template({
                coursewideTopics: this.renderCoursewideTopics(this.model.get('coursewide_categories'), this.model.get('course_wide_children')),
                inlineTopicsHtml: this.renderInlineTopics(this.model),
                always_cohort_inline_discussions:alwaysCohortInlineDiscussions
            }));
            this.processInlineTopics();
            this.toggleDisableClass(this.$('.action-save'), false);
            if (alwaysCohortInlineDiscussions) {
                this.toggleDisableClass(this.$('.inline-cohorts'), false)
            }
        },
        renderCoursewideTopics: function (topics, children) {
            var self = this;
            return _.map(children, function (name) {
                return self.subCategoryTemplate({
                    name: name,
                    id: topics[name].id,
                    is_cohorted: topics[name].is_cohorted,
                    type: 'coursewide'
                });
            }).join('');
        },
        renderInlineTopics: function (category) {
            var category_template = _.template($('#cohort-discussions-category-tpl').html()),
                entry_template = this.subCategoryTemplate,
                is_category_cohorted = false,
                children = category.children || category.get('children'),
                entries = category.entries || category.get('entries'),
                subcategories = category.subcategories || category.get('subcategories');

            return _.map(children, function (name) {
                var html = '', entry;
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
        processInlineTopics: function() {
            $('ul.inline-cohorts').qubit();
        },
        toggleDisableClass: function($element, enable) {
            if (enable) {
                $element.removeClass(disabledClass).attr('aria-disabled', enable);
            } else {
                $element.addClass(disabledClass).attr('aria-disabled', enable);
            }
        },
        changeDiscussionCoursewideCategory: function(event) {
            event.preventDefault();
            this.toggleDisableClass(this.$('.cohort-coursewide-discussions-form .action-save'), true);
        },
        changeAllInlineDiscussions: function(event) {
            event.preventDefault();

            this.toggleDisableClass(this.$('.inline-cohorts'), !($(event.currentTarget).prop('checked')));
            this.processInlineTopics();
            this.toggleDisableClass(this.$('.cohort-inline-discussions-form .action-save'), true);
        },
        changeDiscussionInlineCategory: function(event) {
            var $selectedCategory = $(event.currentTarget);

            if (!$selectedCategory.prop('checked')) {
                $('.check-all-inline-discussions').prop('checked', false);
            }
        },
        changeDiscussionInlineSubCategory: function (event) {
            var $selectedTopic = $(event.currentTarget);
            if (!$selectedTopic.prop('checked')) {
                $('.check-all-inline-discussions').prop('checked', false);
            }
            this.toggleDisableClass(this.$('.cohort-inline-discussions-form .action-save'), true);
        },
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
                fieldData;

            self.getCohortedDiscussions('.check-discussion-subcategory-inline:checked');
            fieldData = {
                content_specific_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };
            this.model.set({always_cohort_inline_discussions: self.$('.check-all-inline-discussions').prop('checked')});
            self.saveForm(fieldData, self.$('.inline-discussion-topics'))
                .done(function () {
                    self.model.fetch().done(function () {
                        self.render();
                        self.showMessage(gettext('Changes Saved.'), self.$('.inline-discussion-topics'));
                    });
                });
        },
        saveCoursewideDiscussionsForm: function (event) {
            var self = this,
                fieldData;

            event.preventDefault();
            self.getCohortedDiscussions('.check-discussion-subcategory-coursewide:checked');
            fieldData = {
                coursewide_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };

            self.saveForm(fieldData, self.$('.coursewide-discussion-topics'))
                .done(function () {
                    self.model.fetch().done(function () {
                         self.render();
                        self.showMessage(gettext('Changes Saved.'), self.$('.coursewide-discussion-topics'));
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
}).call(this, $, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView);
