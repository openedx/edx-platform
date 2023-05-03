(function() {
    'use strict';
    var InstructorDashboardCourseInfo, PendingInstructorTasks;

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    InstructorDashboardCourseInfo = (function() {
        function CourseInfo($section) {
            var courseInfo = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.$course_errors_wrapper = this.$section.find('.course-errors-wrapper');
            if (this.$course_errors_wrapper.length) {
                this.$course_error_toggle = this.$course_errors_wrapper.find('.toggle-wrapper');
                this.$course_error_toggle_text = this.$course_error_toggle.find('h2');
                this.$course_errors = this.$course_errors_wrapper.find('.course-error');
                this.$course_error_toggle_text.text(
                    this.$course_error_toggle_text.text() + (" (' + this.$course_errors.length + ')")
                );
                this.$course_error_toggle.click(function(e) {
                    e.preventDefault();
                    if (courseInfo.$course_errors_wrapper.hasClass('open')) {
                        return courseInfo.$course_errors_wrapper.removeClass('open');
                    } else {
                        return courseInfo.$course_errors_wrapper.addClass('open');
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
    }());

    window.InstructorDashboard.sections.CourseInfo = InstructorDashboardCourseInfo;
}).call(this);
