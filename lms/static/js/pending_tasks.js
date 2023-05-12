// Define an InstructorTaskProgress object for updating a table on the instructor
// dashboard that shows the current background tasks that are currently running
// for the instructor's course.  Any tasks that were running when the page is
// first displayed are passed in as instructor_tasks, and populate the "Pending Instructor
// Task" table. The InstructorTaskProgress is bound to this table, and periodically
// polls the LMS to see if any of the tasks has completed.  Once a task is complete,
// it is not included in any further polling.

(function() {
    // eslint-disable-next-line no-var
    var __bind = function(fn, me) { return function() { return fn.apply(me, arguments); }; };

    this.InstructorTaskProgress = (function() {
        function InstructorTaskProgress(element) {
            this.update_progress = __bind(this.update_progress, this);
            this.get_status = __bind(this.get_status, this);
            this.element = element;
            this.entries = $(element).find('.task-progress-entry');
            if (window.queuePollerID) {
                window.clearTimeout(window.queuePollerID);
            }
            // Hardcode the initial delay before the first refresh to one second:
            window.queuePollerID = window.setTimeout(this.get_status, 1000);
        }

        InstructorTaskProgress.prototype.$ = function(selector) {
            return $(selector, this.element);
        };

        InstructorTaskProgress.prototype.update_progress = function(response) {
            // eslint-disable-next-line no-var
            var _this = this;
            // Response should be a dict with an entry for each requested task_id,
            // with a "task-state" and "in_progress" key and optionally a "message"
            // and a "task_progress.duration" key.
            /* eslint-disable-next-line camelcase, no-var */
            var something_in_progress = false;
            /* eslint-disable-next-line guard-for-in, camelcase, no-undef */
            for (task_id in response) {
                /* eslint-disable-next-line camelcase, no-undef, no-var */
                var task_dict = response[task_id];
                // find the corresponding entry, and update it:
                /* eslint-disable-next-line camelcase, no-undef */
                entry = $(_this.element).find('[data-task-id="' + task_id + '"]');
                /* eslint-disable-next-line camelcase, no-undef */
                entry.find('.task-state').text(task_dict.task_state);
                /* eslint-disable-next-line camelcase, no-var */
                var duration_value = (task_dict.task_progress && task_dict.task_progress.duration_ms
                                        // eslint-disable-next-line camelcase
                                        && Math.round(task_dict.task_progress.duration_ms / 1000)) || 'unknown';
                // eslint-disable-next-line no-undef
                entry.find('.task-duration').text(duration_value);
                /* eslint-disable-next-line camelcase, no-var */
                var progress_value = task_dict.message || '';
                // eslint-disable-next-line no-undef
                entry.find('.task-progress').text(progress_value);
                // if the task is complete, then change the entry so it won't
                // be queried again.  Otherwise set a flag.
                // eslint-disable-next-line camelcase
                if (task_dict.in_progress === true) {
                    // eslint-disable-next-line camelcase
                    something_in_progress = true;
                } else {
                    // eslint-disable-next-line no-undef
                    entry.data('inProgress', 'False');
                }
            }

            // if some entries are still incomplete, then repoll:
            // Hardcode the refresh interval to be every five seconds.
            // TODO: allow the refresh interval to be set.  (And if it is disabled,
            // then don't set the timeout at all.)
            // eslint-disable-next-line camelcase
            if (something_in_progress) {
                window.queuePollerID = window.setTimeout(_this.get_status, 5000);
            } else {
                delete window.queuePollerID;
            }
        };

        InstructorTaskProgress.prototype.get_status = function() {
            /* eslint-disable-next-line no-unused-vars, no-var */
            var _this = this;
            /* eslint-disable-next-line camelcase, no-var */
            var task_ids = [];

            // Construct the array of ids to get status for, by
            // including the subset of entries that are still in progress.
            this.entries.each(function(idx, element) {
                /* eslint-disable-next-line camelcase, no-var */
                var task_id = $(element).data('taskId');
                /* eslint-disable-next-line camelcase, no-var */
                var in_progress = $(element).data('inProgress');
                /* eslint-disable-next-line no-constant-condition, no-cond-assign, camelcase, no-unused-vars */
                if (in_progress = 'True') {
                    // eslint-disable-next-line camelcase
                    task_ids.push(task_id);
                }
            });

            // Make call to get status for these ids.
            // Note that the keyname here ends up with "[]" being appended
            // in the POST parameter that shows up on the Django server.
            // TODO: add error handler.
            /* eslint-disable-next-line camelcase, no-var */
            var ajax_url = '/instructor_task_status/';
            /* eslint-disable-next-line camelcase, no-var */
            var data = {task_ids: task_ids};
            $.post(ajax_url, data).done(this.update_progress);
        };

        return InstructorTaskProgress;
    }());
}).call(this);

// once the page is rendered, create the progress object
/* eslint-disable-next-line no-unused-vars, no-var */
var instructorTaskProgress;
$(document).ready(function() {
    // eslint-disable-next-line no-undef
    instructorTaskProgress = new InstructorTaskProgress($('#task-progress-wrapper'));
});
