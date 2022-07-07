from datetime import timedelta, datetime

from django.db import models, transaction
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import logging

from django_apscheduler import util
from django_apscheduler.util import get_django_internal_datetime

logger = logging.getLogger(__name__)


class DjangoJob(models.Model):
    id = models.CharField(
        max_length=255, primary_key=True, help_text=_("Unique id for this job.")
    )

    next_run_time = models.DateTimeField(
        db_index=True,
        blank=True,
        null=True,
        help_text=_(
            "Date and time at which this job is scheduled to be executed next."
        ),
    )

    job_state = models.BinaryField()

    def __str__(self):
        status = (
            f"next run at: {util.get_local_dt_format(self.next_run_time)}"
            if self.next_run_time
            else "paused"
        )
        return f"{self.id} ({status})"

    class Meta:
        ordering = ("next_run_time",)


class DjangoJobExecutionManager(models.Manager):
    def delete_old_job_executions(self, max_age: int):
        """
        Delete old job executions from the database.

        :param max_age: The maximum age (in seconds). Executions that are older
        than this will be deleted.
        """
        self.filter(run_time__lte=timezone.now() - timedelta(seconds=max_age)).delete()


class DjangoJobExecution(models.Model):
    SENT = "Started execution"
    SUCCESS = "Executed"
    MISSED = "Missed!"
    MAX_INSTANCES = "Max instances!"
    ERROR = "Error!"

    STATUS_CHOICES = [
        (x, x)
        for x in [
            SENT,
            ERROR,
            SUCCESS,
        ]
    ]

    id = models.BigAutoField(
        primary_key=True, help_text=_("Unique ID for this job execution.")
    )

    job = models.ForeignKey(
        DjangoJob,
        on_delete=models.CASCADE,
        help_text=_("The job that this execution relates to."),
    )

    status = models.CharField(
        max_length=50,
        # TODO: Replace this with enumeration types when we drop support for Django 2.2
        # See: https://docs.djangoproject.com/en/dev/ref/models/fields/#field-choices-enum-types
        choices=STATUS_CHOICES,
        help_text=_("The current status of this job execution."),
    )

    run_time = models.DateTimeField(
        db_index=True,
        help_text=_("Date and time at which this job was executed."),
    )

    # We store this value in the DB even though it can be calculated as `finished - run_time`. This allows quick
    # calculation of average durations directly in the database later on.
    duration = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=None,
        null=True,
        help_text=_("Total run time of this job (in seconds)."),
    )

    finished = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=None,
        null=True,
        help_text=_("Timestamp at which this job was finished."),
    )

    exception = models.CharField(
        max_length=1000,
        null=True,
        help_text=_(
            "Details of exception that occurred during job execution (if any)."
        ),
    )

    traceback = models.TextField(
        null=True,
        help_text=_(
            "Traceback of exception that occurred during job execution (if any)."
        ),
    )

    objects = DjangoJobExecutionManager()

    @classmethod
    @util.retry_on_db_operational_error
    def atomic_update_or_create(
        cls,
        lock,
        job_id: str,
        run_time: datetime,
        status: str,
        exception: str = None,
        traceback: str = None,
    ) -> "DjangoJobExecution":
        """
        Uses an APScheduler lock to ensure that only one database entry can be created / updated at a time.

        This keeps django_apscheduler in sync with APScheduler and maintains a 1:1 mapping between APScheduler events
        that are triggered and the corresponding DjangoJobExecution model instances that are persisted to the database.
        :param lock: The lock to use when updating the database - probably obtained by calling _scheduler._create_lock()
        :param job_id: The ID to the APScheduler job that this job execution is for.
        :param run_time: The scheduler runtime for this job execution.
        :param status: The new status for ths job execution.
        :param exception: Details of any exceptions that need to be logged.
        :param traceback: Traceback of any exceptions that occurred while executing the job.
        :return: The ID of the newly created or updated DjangoJobExecution.
        """

        # Ensure that only one update / create can be processed at a time, staying in sync with corresponding
        # scheduler.
        with lock:
            # Convert all datetimes to internal Django format before doing calculations and persisting in the database.
            run_time = get_django_internal_datetime(run_time)

            finished = get_django_internal_datetime(timezone.now())
            duration = (finished - run_time).total_seconds()
            finished = finished.timestamp()

            try:
                with transaction.atomic():
                    job_execution = DjangoJobExecution.objects.select_for_update().get(
                        job_id=job_id, run_time=run_time
                    )

                    if status == DjangoJobExecution.SENT:
                        # Ignore 'submission' events for existing job executions. APScheduler does not appear to
                        # guarantee the order in which events are received, and it is not unusual to receive an
                        # `executed` before the corresponding `submitted` event. We just discard `submitted` events
                        # that are received after the job has already been executed.
                        #
                        # If there are any more instances like this then we probably want to implement a full blown
                        # state machine using something like `pytransitions`
                        # See https://github.com/pytransitions/transitions
                        return job_execution

                    job_execution.finished = finished
                    job_execution.duration = duration
                    job_execution.status = status

                    if exception:
                        job_execution.exception = exception

                    if traceback:
                        job_execution.traceback = traceback

                    job_execution.save()

            except DjangoJobExecution.DoesNotExist:
                # Execution was not created by a 'submit' previously - do so now
                if status == DjangoJobExecution.SENT:
                    # Don't log durations until after job has been submitted for execution
                    finished = None
                    duration = None

                job_execution = DjangoJobExecution.objects.create(
                    job_id=job_id,
                    run_time=run_time,
                    status=status,
                    duration=duration,
                    finished=finished,
                    exception=exception,
                    traceback=traceback,
                )

        return job_execution

    def __str__(self):
        return f"{self.id}: job '{self.job_id}' ({self.status})"

    class Meta:
        ordering = ("-run_time",)
        constraints = [
            UniqueConstraint(
                fields=["job_id", "run_time"], name="unique_job_executions"
            )
        ]
