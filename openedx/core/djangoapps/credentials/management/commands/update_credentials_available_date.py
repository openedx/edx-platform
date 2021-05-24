"""
A manangement command to populate the new available_date field in all CourseCertificates
in credentials. Accomplished by sending the COURSE_CERT_DATE_CHANGE signal accross all
course runs in the LMS to call a new API in credentials that will populate the date if one
is found.

This command is designed to be ran once to backpopulate data. New courses added or any time
the COURSE_CERT_DATE_CHANGE signal fires, the API will automatically be called as a part of
that flow.
"""

import time

from celery.app import shared_task
from celery_utils.logged_task import LoggedTask
from django.core.management.base import BaseCommand
from edx_django_utils.monitoring.internal.code_owner.utils import set_code_owner_attribute

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.signals.signals import COURSE_CERT_DATE_CHANGE


class Command(BaseCommand):
    """
    A command to populate the available_date field in the CourseCertificate model for every
    course run inside of the LMS.
    """

    def handle(self, *args, **options):
        backfill_date_for_all_course_runs.delay()


@shared_task(base=LoggedTask, ignore_result=True)
@set_code_owner_attribute
def backfill_date_for_all_course_runs():
    """
    Pulls a list of every single course run and then sends a cert_date_changed signal. Every 10 courses,
    it will sleep for a time, to create a delay as to not kill credentials/LMS.
    """
    course_run_list = CourseOverview.objects.exclude(self_paced=True).exclude(certificate_available_date=None)
    for index, course_run in enumerate(course_run_list):
        COURSE_CERT_DATE_CHANGE.send_robust(
            sender=None,
            course_key=str(course_run.id),
            available_date=course_run.certificate_available_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        if index % 10 == 0:
            time.sleep(3)
