var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, NotificationModel, NotificationView) {
    'use strict';

    var disabledClass = 'is-disabled';
    edx.groups = edx.groups || {};

    edx.groups.DiscussionTopicsView = Backbone.View.extend({
        events: {
            'change .check-discussion-category': 'changeDiscussionInlineCategory',
            'change .check-discussion-subcategory-inline': 'changeDiscussionInlineSubCategory',
            'change .check-discussion-subcategory-course-wide': 'changeDiscussionCourseWideCategory',
            'click .cohort-course-wide-discussions-form .action-save': 'saveCourseWideDiscussionsForm',
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
                courseWideTopics: this.renderCourseWideTopics(
                    this.model.get('course_wide_categories'),
                    this.model.get('course_wide_children')
                ),
                inlineDiscussionTopics: this.renderInlineTopics(this.model),
                alwaysCohortInlineDiscussions:alwaysCohortInlineDiscussions
            }));

            $('ul.inline-topics').qubit();

            this.toggleDisableClass(this.$('.action-save'), false);
            if (alwaysCohortInlineDiscussions) {
                this.toggleDisableClass(this.$('.inline-topics'), false)
            }
        },
        renderCourseWideTopics: function (topics, children) {
            var self = this;
            return _.map(children, function (name) {
                return self.subCategoryTemplate({
                    name: name,
                    id: topics[name].id,
                    is_cohorted: topics[name].is_cohorted,
                    type: 'course-wide'
                });
            }).join('');
        },
        renderInlineTopics: function (category) {
            var categoryTemplate = _.template($('#cohort-discussions-category-tpl').html()),
                entryTemplate = this.subCategoryTemplate,
                isCategoryCohorted = false,
                children = category.children || category.get('children'),
                entries = category.entries || category.get('entries'),
                subcategories = category.subcategories || category.get('subcategories');

            return _.map(children, function (name) {
                var html = '', entry;
                if (entries && _.has(entries, name)) {
                    entry = entries[name];
                    html = entryTemplate({
                        name: name,
                        id: entry.id,
                        is_cohorted: entry.is_cohorted,
                        type: 'inline'
                    });
                } else { // subcategory
                    html = categoryTemplate({
                        name: name,
                        entries: this.renderInlineTopics(subcategories[name]),
                        isCategoryCohorted: isCategoryCohorted
                    });
                }
                return html;
            }, this).join('');
        },
        toggleDisableClass: function($element, enable) {
            if (enable) {
                $element.removeClass(disabledClass).attr('aria-disabled', enable);
            } else {
                $element.addClass(disabledClass).attr('aria-disabled', enable);
            }
        },
        changeDiscussionCourseWideCategory: function(event) {
            event.preventDefault();
            this.toggleDisableClass(this.$('.cohort-course-wide-discussions-form .action-save'), true);
        },
        changeAllInlineDiscussions: function(event) {
            event.preventDefault();

            this.toggleDisableClass(this.$('.inline-topics'), !($(event.currentTarget).prop('checked')));
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
        saveCourseWideDiscussionsForm: function (event) {
            var self = this,
                fieldData;

            event.preventDefault();
            self.getCohortedDiscussions('.check-discussion-subcategory-course-wide:checked');
            fieldData = {
                course_wide_discussions: true,
                cohorted_discussion_ids: self.cohortedDiscussionTopics
            };

            self.saveForm(fieldData, self.$('.course-wide-discussion-topics'))
                .done(function () {
                    self.model.fetch().done(function () {
                         self.render();
                        self.showMessage(gettext('Changes Saved.'), self.$('.course-wide-discussion-topics'));
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
