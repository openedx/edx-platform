// Define an InstructorTaskProgress object for updating a table on the instructor
// dashboard that shows the current background tasks that are currently running
// for the instructor's course.  Any tasks that were running when the page is
// first displayed are passed in as instructor_tasks, and populate the "Pending Instructor
// Task" table. The InstructorTaskProgress is bound to this table, and periodically
// polls the LMS to see if any of the tasks has completed.  Once a task is complete,
// it is not included in any further polling.

(function() {
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
            var _this = this;
            // Response should be a dict with an entry for each requested task_id,
            // with a "task-state" and "in_progress" key and optionally a "message"
            // and a "task_progress.duration" key.
            var something_in_progress = false;
            for (task_id in response) {
                var task_dict = response[task_id];
                // find the corresponding entry, and update it:
                entry = $(_this.element).find('[data-task-id="' + task_id + '"]');
                entry.find('.task-state').text(task_dict.task_state);
                var duration_value = (task_dict.task_progress && task_dict.task_progress.duration_ms
                                        && Math.round(task_dict.task_progress.duration_ms / 1000)) || 'unknown';
                entry.find('.task-duration').text(duration_value);
                var progress_value = task_dict.message || '';
                entry.find('.task-progress').text(progress_value);
                // if the task is complete, then change the entry so it won't
                // be queried again.  Otherwise set a flag.
                if (task_dict.in_progress === true) {
                    something_in_progress = true;
                } else {
                    entry.data('inProgress', 'False');
                }
            }

            // if some entries are still incomplete, then repoll:
            // Hardcode the refresh interval to be every five seconds.
            // TODO: allow the refresh interval to be set.  (And if it is disabled,
            // then don't set the timeout at all.)
            if (something_in_progress) {
                window.queuePollerID = window.setTimeout(_this.get_status, 5000);
            } else {
                delete window.queuePollerID;
            }
        };

        InstructorTaskProgress.prototype.get_status = function() {
            var _this = this;
            var task_ids = [];

            // Construct the array of ids to get status for, by
            // including the subset of entries that are still in progress.
            this.entries.each(function(idx, element) {
                var task_id = $(element).data('taskId');
                var in_progress = $(element).data('inProgress');
                if (in_progress = 'True') {
                    task_ids.push(task_id);
                }
            });

            // Make call to get status for these ids.
            // Note that the keyname here ends up with "[]" being appended
            // in the POST parameter that shows up on the Django server.
            // TODO: add error handler.
            var ajax_url = '/instructor_task_status/';
            var data = {'task_ids': task_ids};
            $.post(ajax_url, data).done(this.update_progress);
        };

        return InstructorTaskProgress;
    })();
}).call(this);

// once the page is rendered, create the progress object
var instructorTaskProgress;
$(document).ready(function() {
    instructorTaskProgress = new InstructorTaskProgress($('#task-progress-wrapper'));
});

