"""
   Task that update ProgressModules table.
"""
from djcelery import celery
from celery import Task, current_task
from django.core.cache import cache
from xmodule.modulestore.django import modulestore
from pgreport.views import update_pgreport_table, create_pgreport_csv
from pgreport.views import UserDoesNotExists
from datetime import datetime
import uuid
from functools import partial
import os
import socket


class ProgressreportException(Exception):
    pass

 
class TaskState(object):
    """State of task."""

    def __init__(self, task_name, course_id):
        """Initialize."""
        self.key = "celery_task_state-" + task_name
        self.course_id = course_id

    @property
    def is_active(self):
        """Property of state."""
        state = cache.get(key=self.key, default={})
        if state is not None and self.course_id in state:
            return True

        return False 

    def set_task_state(self):
        """Set task state."""
        state = cache.get(key=self.key, default={})
        if state:
            state.update({self.course_id: datetime.now()})
        else:
            state = {self.course_id: datetime.now()}
        cache.set(key=self.key, value=state)

    def delete_task_state(self):
        """Delete task state."""
        state = cache.get(key=self.key, default={})
        state.pop(self.course_id, None)
        if not state:
            cache.delete(key=self.key)
        else:
            cache.set(key=self.key, value=state)


class BaseProgressReportTask(Task):
    """Base class for progress report."""
    abstract = True

    def _delete_task_state(self, args):
        """Delete task state."""
        if args:
            course_id = args[1]
        else:
            course_id = "AllCourses"

        task_name = self.name
        task_state = TaskState(task_name, course_id)
        task_state.delete_task_state()

    def on_success(self, retval, task_id, args, kwargs):
        """Delete task state on success."""
        self._delete_task_state(args)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Delete task state on failure."""
        self._delete_task_state(args)


class ProgressReportTask(object):
    """Task class for progress report."""

    def __init__(self, func):
        """Initialize"""
        self.task_func = func
        if not hasattr(func, 'apply_async') or not hasattr(func, 'AsyncResult'):
            raise ProgressreportException("Funcion is not celery task.")

        self.task_name = func.name
        self.modulestore_name = 'default'

    def send_task(self, course_id):
        """Send task."""
        task_state = TaskState(self.task_name, course_id)
        if task_state.is_active:
            print "Task is already running. (%s, %s)" % (self.task_name, course_id)
            return

        task_id = str(uuid.uuid4())
        result = self.task_func.apply_async(
            args=(task_id, unicode(course_id)), task_id=task_id, expires=23.5*60*60, retry=False
        )
        task_state.set_task_state()
        print "Send task (task_id: %s)" % (result.id)

    def send_tasks(self):
        """Send task for all of active courses."""
        store = modulestore(self.modulestore_name)

        for course in store.get_courses():
            if course.has_started() and not course.has_ended():
                self.send_task(course.id)

    def show_task_status(self, task_id):
        """Show current state of task."""
        result = self.task_func.AsyncResult(task_id)
        if result.state == "PENDING":
            print "Task not found or PENDING state"
        else:
            print "Current State: %s, %s" % (result.state, result.info)

    def show_task_list(self):
        """A view that returns active tasks"""
        stats = celery.control.inspect()
        print "*** Active queues ***"

        for queue, states in stats.active().items():
            if states:
                print "%s: [" % (queue)

                for state in states:
                    task_args = state['args']
                    task_id = state['id']
                    task_name = state['name']
                    worker_pid = state['worker_pid']
                    print " * Task id: %s, Task args: %s," % (
                        task_id, task_args),
                    print " Task name: %s, Worker pid: %s" % (
                        task_name, worker_pid)

                print "]"
            else:
                print "%s: []" % (queue)

    def revoke_task(self, task_id):
        """Send revoke signal to all workers."""
        result = self.task_func.AsyncResult(task_id)
        result.revoke(terminate=True)


@celery.task(base=BaseProgressReportTask)
def update_table_task(task_id, course_id):
    """Update progress_modules."""
    update_state = partial(
        update_table_task.update_state, task_id=task_id,
        meta={"hostname": socket.gethostname(), "pid": os.getpid()}
    )

    try: 
        update_pgreport_table(course_id, update_state)
    except UserDoesNotExists as e:
        return "%s (%s)" % (e, course_id)

    return "Update complete!!! (%s)" % (course_id)


@celery.task(base=BaseProgressReportTask)
def create_report_task(task_id, course_id):
    """Create progress report."""
    update_state = partial(
        create_report_task.update_state, task_id=task_id, 
        meta={"hostname": socket.gethostname(), "pid": os.getpid()}
    )

    try: 
        create_pgreport_csv(course_id, update_state)
    except UserDoesNotExists as e:
        return "%s (%s)" % (e, course_id)

    return "Create complete!!! (%s)" % (course_id)


@celery.task(base=BaseProgressReportTask)
def update_table_task_for_active_course(course_id=None):
    """Update progress_modules table for active course."""
    task = ProgressReportTask(update_table_task)
    task.send_tasks()
