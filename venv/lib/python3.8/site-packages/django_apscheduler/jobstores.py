import logging
import pickle
import warnings
from typing import Union, List

from apscheduler import events
from apscheduler.events import JobSubmissionEvent, JobExecutionEvent
from apscheduler.job import Job as AppSchedulerJob
from apscheduler.jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.base import BaseScheduler

from django import db
from django.db import transaction, IntegrityError

from django_apscheduler import util
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django_apscheduler.util import (
    get_apscheduler_datetime,
    get_django_internal_datetime,
)

logger = logging.getLogger(__name__)


class DjangoResultStoreMixin:
    """Mixin class that adds the ability for a JobStore to store job execution results in the Django database"""

    lock = None

    def start(self, scheduler, alias):
        super().start(scheduler, alias)

        # Use the same type of lock as the scheduler to ensure that only one APScheduler event is processed at a time.
        DjangoResultStoreMixin.lock = self._scheduler._create_lock()

        self.register_event_listeners()

    @classmethod
    def handle_submission_event(cls, event: JobSubmissionEvent):
        """
        Create and return new job execution instance in the database when the job is submitted to the scheduler.

        :param event: JobExecutionEvent instance
        :return: DjangoJobExecution ID or None if the job execution could not be logged.
        """
        try:
            if event.code == events.EVENT_JOB_SUBMITTED:
                # Start logging a new job execution
                job_execution = DjangoJobExecution.atomic_update_or_create(
                    cls.lock,
                    event.job_id,
                    event.scheduled_run_times[0],
                    DjangoJobExecution.SENT,
                )

            elif event.code == events.EVENT_JOB_MAX_INSTANCES:
                status = DjangoJobExecution.MAX_INSTANCES

                exception = (
                    f"Execution of job '{event.job_id}' skipped: maximum number of running "
                    f"instances reached!"
                )

                job_execution = DjangoJobExecution.atomic_update_or_create(
                    cls.lock,
                    event.job_id,
                    event.scheduled_run_times[0],
                    status,
                    exception=exception,
                )
            else:
                raise NotImplementedError(
                    f"Don't know how to handle JobSubmissionEvent '{event.code}'. Expected "
                    f"one of '{[events.EVENT_JOB_SUBMITTED, events.EVENT_JOB_MAX_INSTANCES]}'."
                )
        except IntegrityError:
            logger.warning(
                f"Job '{event.job_id}' no longer exists! Skipping logging of job execution..."
            )
            return None

        return job_execution.id

    @classmethod
    def handle_execution_event(cls, event: JobExecutionEvent) -> Union[int, None]:
        """
        Store "successful" job execution status in the database.

        :param event: JobExecutionEvent instance
        :return: DjangoJobExecution ID or None if the job execution could not be logged.
        """
        if event.code != events.EVENT_JOB_EXECUTED:
            raise NotImplementedError(
                f"Don't know how to handle JobExecutionEvent '{event.code}'. Expected "
                f"'{events.EVENT_JOB_EXECUTED}'."
            )

        try:
            job_execution = DjangoJobExecution.atomic_update_or_create(
                cls.lock,
                event.job_id,
                event.scheduled_run_time,
                DjangoJobExecution.SUCCESS,
            )
        except IntegrityError:
            logger.warning(
                f"Job '{event.job_id}' no longer exists! Skipping logging of job execution..."
            )
            return None

        return job_execution.id

    @classmethod
    def handle_error_event(cls, event: JobExecutionEvent) -> Union[int, None]:
        """
        Store "failed" job execution status in the database.

        :param event: JobExecutionEvent instance
        :return: DjangoJobExecution ID or None if the job execution could not be logged.
        """
        try:
            if event.code == events.EVENT_JOB_ERROR:

                if event.exception:
                    exception = str(event.exception)
                    traceback = str(event.traceback)
                else:
                    exception = f"Job '{event.job_id}' raised an error!"
                    traceback = None

                job_execution = DjangoJobExecution.atomic_update_or_create(
                    cls.lock,
                    event.job_id,
                    event.scheduled_run_time,
                    DjangoJobExecution.ERROR,
                    exception=exception,
                    traceback=traceback,
                )

            elif event.code == events.EVENT_JOB_MISSED:
                # Job execution will not have been logged yet - do so now
                status = DjangoJobExecution.MISSED
                exception = f"Run time of job '{event.job_id}' was missed!"

                job_execution = DjangoJobExecution.atomic_update_or_create(
                    cls.lock,
                    event.job_id,
                    event.scheduled_run_time,
                    status,
                    exception=exception,
                )

            else:
                raise NotImplementedError(
                    f"Don't know how to handle JobExecutionEvent '{event.code}'. Expected "
                    f"one of '{[events.EVENT_JOB_ERROR, events.EVENT_JOB_MAX_INSTANCES, events.EVENT_JOB_MISSED]}'."
                )
        except IntegrityError:
            logger.warning(
                f"Job '{event.job_id}' no longer exists! Skipping logging of job execution..."
            )
            return None

        return job_execution.id

    def register_event_listeners(self):
        """
        Register various event listeners.

        See: https://github.com/agronholm/apscheduler/blob/master/docs/modules/events.rst for details on which event
        class is used for each event code.

        """
        self._scheduler.add_listener(
            self.handle_submission_event,
            events.EVENT_JOB_SUBMITTED | events.EVENT_JOB_MAX_INSTANCES,
        )

        self._scheduler.add_listener(
            self.handle_execution_event, events.EVENT_JOB_EXECUTED
        )

        self._scheduler.add_listener(
            self.handle_error_event,
            events.EVENT_JOB_ERROR | events.EVENT_JOB_MISSED,
        )


class DjangoJobStore(DjangoResultStoreMixin, BaseJobStore):
    """
    Stores jobs in a Django database. Based on APScheduler's `MongoDBJobStore`.

    See: https://github.com/agronholm/apscheduler/blob/master/apscheduler/jobstores/mongodb.py

    :param int pickle_protocol: pickle protocol level to use (for serialization), defaults to the
           highest available
    """

    def __init__(self, pickle_protocol: int = pickle.HIGHEST_PROTOCOL):
        super().__init__()
        self.pickle_protocol = pickle_protocol

    @util.retry_on_db_operational_error
    def lookup_job(self, job_id: str) -> Union[None, AppSchedulerJob]:
        try:
            job_state = DjangoJob.objects.get(id=job_id).job_state
            return self._reconstitute_job(job_state) if job_state else None

        except DjangoJob.DoesNotExist:
            return None

    def get_due_jobs(self, now) -> List[AppSchedulerJob]:
        dt = get_django_internal_datetime(now)
        return self._get_jobs(next_run_time__lte=dt)

    @util.retry_on_db_operational_error
    def get_next_run_time(self):
        try:
            job = DjangoJob.objects.filter(next_run_time__isnull=False).earliest(
                "next_run_time"
            )
            return get_apscheduler_datetime(job.next_run_time, self._scheduler)
        except DjangoJob.DoesNotExist:
            # No active jobs - OK
            return None

    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)

        return jobs

    @util.retry_on_db_operational_error
    def add_job(self, job: AppSchedulerJob):
        with transaction.atomic():
            try:
                return DjangoJob.objects.create(
                    id=job.id,
                    next_run_time=get_django_internal_datetime(job.next_run_time),
                    job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol),
                )
            except IntegrityError:
                raise ConflictingIdError(job.id)

    @util.retry_on_db_operational_error
    def update_job(self, job: AppSchedulerJob):
        # Acquire lock for update
        with transaction.atomic():
            try:
                db_job = DjangoJob.objects.get(id=job.id)

                db_job.next_run_time = get_django_internal_datetime(job.next_run_time)
                db_job.job_state = pickle.dumps(
                    job.__getstate__(), self.pickle_protocol
                )

                db_job.save()

            except DjangoJob.DoesNotExist:
                raise JobLookupError(job.id)

    @util.retry_on_db_operational_error
    def remove_job(self, job_id: str):
        try:
            DjangoJob.objects.get(id=job_id).delete()
        except DjangoJob.DoesNotExist:
            raise JobLookupError(job_id)

    @util.retry_on_db_operational_error
    def remove_all_jobs(self):
        # Implicit: will also delete all DjangoJobExecutions due to on_delete=models.CASCADE
        DjangoJob.objects.all().delete()

    def shutdown(self):
        db.connection.close()

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job = AppSchedulerJob.__new__(AppSchedulerJob)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias

        return job

    @util.retry_on_db_operational_error
    def _get_jobs(self, **filters):
        jobs = []
        failed_job_ids = set()

        job_states = DjangoJob.objects.filter(**filters).values_list("id", "job_state")
        for job_id, job_state in job_states:
            try:
                jobs.append(self._reconstitute_job(job_state))
            # TODO: Make this except clause more specific
            except Exception:
                self._logger.exception(
                    f"Unable to restore job '{job_id}'. Removing it..."
                )
                failed_job_ids.add(job_id)

        # Remove all the jobs we failed to restore
        if failed_job_ids:
            logger.warning(f"Removing failed jobs: {failed_job_ids}")
            DjangoJob.objects.filter(id__in=failed_job_ids).delete()

        return jobs

    def __repr__(self):
        return f"<{self.__class__.__name__}(pickle_protocol={self.pickle_protocol})>"


class DjangoMemoryJobStore(DjangoResultStoreMixin, MemoryJobStore):
    """
    Adds the DjangoResultStoreMixin to the standard MemoryJobStore so that job executions can be
    logged to the Django database.
    """

    pass


def register_events(scheduler, result_storage=None):
    # TODO: Remove this deprecated function in release 1.0
    # DjangoResultStoreMixin now takes care of registering event listeners automatically when the scheduler is started.
    warnings.warn(
        "'register_events' is deprecated since version 0.4.0. Please remove all references from your code.",
        DeprecationWarning,
    )
    pass


def register_job(scheduler: BaseScheduler, *args, **kwargs) -> callable:
    """
    Helper decorator for job registration.

    Automatically fills id parameter to prevent jobs duplication.
    See this comment for explanation: https://github.com/jcass77/django-apscheduler/pull/9#issuecomment-342074372

    Usage example::

        @register_job(scheduler, "interval", seconds=1)
        def dummy_job():
            print("I'm a job!")

    :param scheduler: Scheduler instance
    :param args, kwargs: Params, will be passed to scheduler.add_job method. See :func:`BaseScheduler.add_job`
    """

    def wrapper_register_job(func):
        # TODO: Remove this deprecated function in release 1.0
        warnings.warn(
            "The 'register_job' decorator is deprecated since version 0.5.0. Please use APScheduler's add_job() method "
            "or @scheduled_job decorator instead.",
            DeprecationWarning,
        )

        kwargs.setdefault("id", f"{func.__module__}.{func.__name__}")
        scheduler.add_job(func, *args, **kwargs)

        return func

    return wrapper_register_job
