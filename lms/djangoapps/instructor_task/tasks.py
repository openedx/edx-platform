"""
This file contains tasks that are designed to perform background operations on the
running state of a course.



"""
from celery import task
from instructor_task.tasks_helper import (update_problem_module_state,
                                          rescore_problem_module_state,
                                          reset_attempts_module_state,
                                          delete_problem_module_state)


@task
def rescore_problem(entry_id, xmodule_instance_args):
    """Rescores problem in `course_id`.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    `course_id` identifies the course.
    `task_input` should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)
      'student': the identifier (username or email) of a particular user whose
          problem submission should be rescored.  If not specified, all problem
          submissions will be rescored.

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    action_name = 'rescored'
    update_fcn = rescore_problem_module_state
    filter_fcn = lambda(modules_to_update): modules_to_update.filter(state__contains='"done": true')
    return update_problem_module_state(entry_id,
                                       update_fcn, action_name, filter_fcn=filter_fcn,
                                       xmodule_instance_args=xmodule_instance_args)


@task
def reset_problem_attempts(entry_id, xmodule_instance_args):
    """Resets problem attempts to zero for `problem_url` in `course_id` for all students.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    `course_id` identifies the course.
    `task_input` should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    action_name = 'reset'
    update_fcn = reset_attempts_module_state
    return update_problem_module_state(entry_id,
                                       update_fcn, action_name, filter_fcn=None,
                                       xmodule_instance_args=xmodule_instance_args)


@task
def delete_problem_state(entry_id, xmodule_instance_args):
    """Deletes problem state entirely for `problem_url` in `course_id` for all students.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    `course_id` identifies the course.
    `task_input` should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    action_name = 'deleted'
    update_fcn = delete_problem_module_state
    return update_problem_module_state(entry_id,
                                       update_fcn, action_name, filter_fcn=None,
                                       xmodule_instance_args=xmodule_instance_args)
