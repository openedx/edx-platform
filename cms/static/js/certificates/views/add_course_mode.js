define([
    'underscore',
    'gettext',
    'js/views/baseview',
    'common/js/components/views/feedback_notification',
    'text!templates/course-modes.underscore',
    'edx-ui-toolkit/js/utils/html-utils'
],
function(_, gettext, BaseView, NotificationView, CourseModes, HtmlUtils) {
    'use strict';

    var AddCourseMode = BaseView.extend({
        el: $('.wrapper-certificates'),
        events: {
            'click .add-course-mode': 'addCourseMode'
        },

        initialize: function(options) {
            this.enableCourseModeCreation = options.enableCourseModeCreation;
            this.courseModeCreationUrl = options.courseModeCreationUrl;
            this.courseId = options.courseId;
        },

        render: function() {
            HtmlUtils.setHtml(this.$el, HtmlUtils.template(CourseModes)({
                enableCourseModeCreation: this.enableCourseModeCreation,
                courseModeCreationUrl: this.courseModeCreationUrl,
                courseId: this.courseId
            }));
            return this;
        },

        addCourseMode: function() {
            var notification = new NotificationView.Mini({
                title: gettext('Enabling honor course mode')
            });
            var username = $('.account-username')[0].innerText;
            $.ajax({
                url: this.courseModeCreationUrl + '?username=' + username,
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    course_id: this.courseId,
                    mode_slug: 'honor',
                    mode_display_name: 'Honor',
                    currency: 'usd'
                }),
                type: 'POST',
                beforeSend: function() {
                    notification.show();
                },
                success: function() {
                    notification.hide();
                    location.reload();
                }
            });
        },

        show: function() {
            this.render();
        },

        remove: function() {
            this.enableCourseModeCreation = false;
            this.$el.empty();
            return this;
        }
    });
    return AddCourseMode;
});
