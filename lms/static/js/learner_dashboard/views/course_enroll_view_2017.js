(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!../../../templates/learner_dashboard/course_enroll_2017.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             pageTpl
         ) {
             return Backbone.View.extend({
                 className: 'course-enroll-view',

                 tpl: HtmlUtils.template(pageTpl),

                 events: {
                     'click .enroll-button': 'handleEnroll'
                 },

                 initialize: function(options) {
                     this.$parentEl = options.$parentEl;
                     this.enrollModel = options.enrollModel;
                     this.urlModel = options.urlModel;
                     this.render();
                 },

                 render: function() {
                     var filledTemplate;
                     if (this.$parentEl && this.enrollModel) {
                         filledTemplate = this.tpl(this.model.toJSON());
                         HtmlUtils.setHtml(this.$el, filledTemplate);
                         HtmlUtils.setHtml(this.$parentEl, HtmlUtils.HTML(this.$el));
                     }
                     this.postRender();
                 },

                 postRender: function() {
                     if (this.urlModel) {
                         this.trackSelectionUrl = this.urlModel.get('track_selection_url');
                     }
                 },

                 handleEnroll: function() {
                     // Enrollment click event handled here
                     var courseRunKey = $('.run-select').val();
                     this.model.updateCourseRun(courseRunKey);
                     if (!this.model.get('is_enrolled')) {
                         // Create the enrollment.
                         this.enrollModel.save({
                             course_id: courseRunKey
                         }, {
                             success: _.bind(this.enrollSuccess, this),
                             error: _.bind(this.enrollError, this)
                         });
                     }
                 },

                 enrollSuccess: function() {
                     var courseRunKey = this.model.get('course_run_key');
                     window.analytics.track('edx.bi.user.program-details.enrollment');
                     if (this.trackSelectionUrl) {
                         // Go to track selection page
                         this.redirect(this.trackSelectionUrl + courseRunKey);
                     } else {
                         this.model.set({
                             is_enrolled: true
                         });
                     }
                 },

                 enrollError: function(model, response) {
                     if (response.status === 403 && response.responseJSON.user_message_url) {
                        /**
                         * Check if we've been blocked from the course
                         * because of country access rules.
                         * If so, redirect to a page explaining to the user
                         * why they were blocked.
                         */
                         this.redirect(response.responseJSON.user_message_url);
                     } else if (this.trackSelectionUrl) {
                        /**
                         * Otherwise, go to the track selection page as usual.
                         * This can occur, for example, when a course does not
                         * have a free enrollment mode, so we can't auto-enroll.
                         */
                         this.redirect(this.trackSelectionUrl + this.model.get('course_run_key'));
                     }
                 },

                 redirect: function(url) {
                     window.location.href = url;
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
