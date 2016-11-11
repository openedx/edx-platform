(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext', 'js/groups/views/cohort_discussions',
        'edx-ui-toolkit/js/utils/html-utils'],
            function($, _, Backbone, gettext, CohortDiscussionConfigurationView, HtmlUtils) {
                var CourseWideDiscussionsView = CohortDiscussionConfigurationView.extend({
                    events: {
                        'change .check-discussion-subcategory-course-wide': 'discussionCategoryStateChanged',
                        'click .cohort-course-wide-discussions-form .action-save': 'saveCourseWideDiscussionsForm'
                    },

                    initialize: function(options) {
                        this.template = HtmlUtils.template($('#cohort-discussions-course-wide-tpl').text());
                        this.cohortSettings = options.cohortSettings;
                    },

                    render: function() {
                        HtmlUtils.setHtml(this.$('.cohort-course-wide-discussions-nav'), this.template({
                            courseWideTopicsHtml: this.getCourseWideDiscussionsHtml(
                                this.model.get('course_wide_discussions')
                            )
                        }));
                        this.setDisabled(this.$('.cohort-course-wide-discussions-form .action-save'), true);
                    },

                    /**
                     * Returns the html list for course-wide discussion topics.
                     * @param {object} courseWideDiscussions - course-wide discussions object from server.
                     * @returns {HtmlSnippet} - HTML list for course-wide discussion topics.
                     */
                    getCourseWideDiscussionsHtml: function(courseWideDiscussions) {
                        var subCategoryTemplate = HtmlUtils.template($('#cohort-discussions-subcategory-tpl').html()),
                            entries = courseWideDiscussions.entries,
                            children = courseWideDiscussions.children;

                        return HtmlUtils.joinHtml.apply(this, _.map(children, function(child) {
                            // child[0] is the category name, child[1] is the type.
                            // For course wide discussions, the type is always 'entry'
                            var name = child[0],
                                entry = entries[name];
                            return subCategoryTemplate({
                                name: name,
                                id: entry.id,
                                is_cohorted: entry.is_cohorted,
                                type: 'course-wide'
                            });
                        }));
                    },

                    /**
                     * Enables the save button for course-wide discussions.
                     */
                    discussionCategoryStateChanged: function(event) {
                        event.preventDefault();
                        this.setDisabled(this.$('.cohort-course-wide-discussions-form .action-save'), false);
                    },

                    /**
                     * Sends the cohorted_course_wide_discussions to the server and renders the view.
                     */
                    saveCourseWideDiscussionsForm: function(event) {
                        event.preventDefault();

                        var self = this,
                            courseWideCohortedDiscussions = self.getCohortedDiscussions(
                                '.check-discussion-subcategory-course-wide:checked'
                            ),
                            fieldData = {cohorted_course_wide_discussions: courseWideCohortedDiscussions};

                        self.saveForm(self.$('.course-wide-discussion-topics'), fieldData)
                        .done(function() {
                            self.model.fetch()
                                .done(function() {
                                    self.render();
                                    self.showMessage(gettext('Your changes have been saved.'), self.$('.course-wide-discussion-topics'));
                                }).fail(function() {
                                    var errorMessage = gettext("We've encountered an error. Refresh your browser and then try again.");
                                    self.showMessage(errorMessage, self.$('.course-wide-discussion-topics'), 'error');
                                });
                        });
                    }

                });
                return CourseWideDiscussionsView;
            });
}).call(this, define || RequireJS.define);
