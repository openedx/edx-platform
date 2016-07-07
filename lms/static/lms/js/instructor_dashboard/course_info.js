/**
 * Course Info Section
 *
 * imports from other modules.
 * wrap in (-> ... apply) to defer evaluation
 * such that the value can be defined later than this assignment (file load order).
 */
(function() {
    'use strict';

    var CourseInfo, PendingInstructorTasks;

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    /**
     * A typical section object.
     *
     * This is constructed with $section, a JQuery object
     * which holds the section body container.
     */
    CourseInfo = (function() {

        function CourseInfo($section) {
            var _this = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.$course_errors_wrapper = this.$section.find('.course-errors-wrapper');
            if (this.$course_errors_wrapper.length) {
                this.$course_error_toggle = this.$course_errors_wrapper.find('.toggle-wrapper');
                this.$course_error_toggle_text = this.$course_error_toggle.find('h2');
                this.$course_errors = this.$course_errors_wrapper.find('.course-error');
                this.$course_error_toggle_text.text(
                    this.$course_error_toggle_text.text() + (' (' + this.$course_errors.length + ')')
                );
                this.$course_error_toggle.click(function(e) {
                    e.preventDefault();
                    if (_this.$course_errors_wrapper.hasClass('open')) {
                        return _this.$course_errors_wrapper.removeClass('open');
                    } else {
                        return _this.$course_errors_wrapper.addClass('open');
                    }
                });
            }
        }

        CourseInfo.prototype.onClickTitle = function() {
            return this.instructor_tasks.task_poller.start();
        };

        CourseInfo.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };

        return CourseInfo;

    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        CourseInfo: CourseInfo
    });

}).call(this);
