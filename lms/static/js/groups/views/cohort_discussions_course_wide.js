var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, CohortDiscussionsView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CourseWideDiscussionsView = CohortDiscussionsView.extend({
        events: {
            'change .check-discussion-subcategory-course-wide': 'changeCourseWideDiscussionCategory',
            'click .cohort-course-wide-discussions-form .action-save': 'saveCourseWideDiscussionsForm'
        },

        initialize: function (options) {
            this.template = _.template($('#cohort-discussions-course-wide-tpl').text());
            this.cohortSettings = options.cohortSettings;
        },

        render: function () {
            this.$('.cohort-course-wide-discussions-nav').html(this.template({
                courseWideTopics: this.getCourseWideDiscussions(
                    this.model.get('course_wide_discussions')
                )
            }));
            this.setDisabled(this.$('.cohort-course-wide-discussions-form .action-save'), true);
        },

        /**
        Returns the html list for course-wide discussion topics.

        Args:
            courseWideDiscussions (object): course-wide discussions object from server
                with two attributes 'children' & 'entries'.

        Returns:
            HTML list for course-wide discussion topics.
        **/
        getCourseWideDiscussions: function (courseWideDiscussions) {
            var subCategoryTemplate = _.template($('#cohort-discussions-subcategory-tpl').html()),
                entries = courseWideDiscussions.entries,
                children = courseWideDiscussions.children;

            return _.map(children, function (name) {
                var entry = entries[name];
                return subCategoryTemplate({
                    name: name,
                    id: entry.id,
                    is_cohorted: entry.is_cohorted,
                    type: 'course-wide'
                });
            }).join('');
        },

        /**
        Enables the save button for course-wide discussions.
        **/
        changeCourseWideDiscussionCategory: function(event) {
            event.preventDefault();
            this.setDisabled(this.$('.cohort-course-wide-discussions-form .action-save'), false);
        },

        /**
        Sends the cohorted_course_wide_discussions to the server and renders the view.
        **/
        saveCourseWideDiscussionsForm: function (event) {
            event.preventDefault();

            var self = this;
            var courseWideCohortedDiscussions = self.getCohortedDiscussions(
                '.check-discussion-subcategory-course-wide:checked'
            );

            this.cohortSettings.set({cohorted_course_wide_discussions:courseWideCohortedDiscussions});
            self.saveForm(self.$('.course-wide-discussion-topics'))
                .done(function () {
                    self.model.fetch().done(function () {
                         self.render();
                        self.showMessage(gettext('Changes Saved.'), self.$('.course-wide-discussion-topics'));
                    });
                });
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text, edx.groups.CohortDiscussionsView);
