"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
 3. Add the migration file created in edx-platform/lms/djangoapps/instructor_task/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.contrib.auth.models import User
from django.db import models


class InstructorTask(models.Model):
    """
    Stores information about background tasks that have been submitted to
    perform work by an instructor (or course staff).
    Examples include grading and rescoring.

    `task_type` identifies the kind of task being performed, e.g. rescoring.
    `course_id` uses the course run's unique id to identify the course.
    `task_input` stores input arguments as JSON-serialized dict, for reporting purposes.
        Examples include url of problem being rescored, id of student if only one student being rescored.
    `task_key` stores relevant input arguments encoded into key value for testing to see
           if the task is already running (together with task_type and course_id).

    `task_id` stores the id used by celery for the background task.
    `task_state` stores the last known state of the celery task
    `task_output` stores the output of the celery task.
        Format is a JSON-serialized dict.  Content varies by task_type and task_state.

    `requester` stores id of user who submitted the task
    `created` stores date that entry was first created
    `updated` stores date that entry was last modified
    """
    task_type = models.CharField(max_length=50, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    task_key = models.CharField(max_length=255, db_index=True)
    task_input = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, db_index=True)  # max_length from celery_taskmeta
    task_state = models.CharField(max_length=50, null=True, db_index=True)  # max_length from celery_taskmeta
    task_output = models.CharField(max_length=1024, null=True)
    requester = models.ForeignKey(User, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return 'InstructorTask<%r>' % ({
            'task_type': self.task_type,
            'course_id': self.course_id,
            'task_input': self.task_input,
            'task_id': self.task_id,
            'task_state': self.task_state,
            'task_output': self.task_output,
        },)

    def __unicode__(self):
        return unicode(repr(self))
