import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import pageTpl from '../../../templates/learner_dashboard/course_enroll.underscore';

class CourseEnrollView extends Backbone.View {
    constructor(options) {
        const defaults = {
            className: 'course-enroll-view',
            events: {
                'click .enroll-button': 'handleEnroll',
                'change .run-select': 'updateEnrollUrl',
            },
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(pageTpl);
        this.$parentEl = options.$parentEl;
        this.enrollModel = options.enrollModel;
        this.urlModel = options.urlModel;
        this.collectionCourseStatus = options.collectionCourseStatus;
        this.render();
    }

    render() {
        let filledTemplate;
        const context = this.model.toJSON();
        if (this.$parentEl && this.enrollModel) {
            context.collectionCourseStatus = this.collectionCourseStatus;
            filledTemplate = this.tpl(context);
            HtmlUtils.setHtml(this.$el, filledTemplate);
            HtmlUtils.setHtml(this.$parentEl, HtmlUtils.HTML(this.$el));
        }
        this.postRender();
    }

    postRender() {
        if (this.urlModel) {
            this.trackSelectionUrl = this.urlModel.get('track_selection_url');
        }
    }

    handleEnroll() {
    // Enrollment click event handled here
        if (this.model.get('is_mobile_only') !== true) {
            const courseRunKey = this.$el.find('.run-select').val() || this.model.get('course_run_key');
            this.model.updateCourseRun(courseRunKey);
            if (this.model.get('is_enrolled')) {
                // Create the enrollment.
                this.enrollModel.save({
                    course_id: courseRunKey,
                }, {
                    success: this.enrollSuccess.bind(this),
                    error: this.enrollError.bind(this),
                });
            }
        }
    }

    enrollSuccess() {
        const courseRunKey = this.model.get('course_run_key');
        window.analytics.track('edx.bi.user.program-details.enrollment');
        if (this.trackSelectionUrl) {
            // Go to track selection page
            CourseEnrollView.redirect(this.trackSelectionUrl + courseRunKey);
        } else {
            this.model.set({
                is_enrolled: true,
            });
        }
    }

    enrollError(model, response) {
        if (response.status === 403 && response.responseJSON.user_message_url) {
            /**
       * Check if we've been blocked from the course
       * because of country access rules.
       * If so, redirect to a page explaining to the user
       * why they were blocked.
       */
            CourseEnrollView.redirect(response.responseJSON.user_message_url);
        } else if (this.trackSelectionUrl) {
            /**
       * Otherwise, go to the track selection page as usual.
       * This can occur, for example, when a course does not
       * have a free enrollment mode, so we can't auto-enroll.
       */
            CourseEnrollView.redirect(this.trackSelectionUrl + this.model.get('course_run_key'));
        }
    }

    updateEnrollUrl() {
        if (this.model.get('is_mobile_only') === true) {
            const courseRunKey = $('.run-select').val();
            const href = `edxapp://enroll?course_id=${courseRunKey}&email_opt_in=true`;
            $('.enroll-course-button').attr('href', href);
        }
    }

    static redirect(url) {
        window.location.href = url;
    }
}

export default CourseEnrollView;
