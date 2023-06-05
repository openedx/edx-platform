

import csv
import logging
from datetime import datetime, timedelta
from os import remove

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from pytz import utc

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseAccessRole

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms export_staff_users -d 7 --settings=devstack_docker
        $ ./manage.py lms export_staff_users --days 7 --settings=devstack_docker
        $ ./manage.py lms export_staff_users --days 7 --dry true --settings=devstack_docker
    """

    help = """
    This command will export a csv of all users who have logged in within the given days and
    have staff access role in active courses (Courses with end date in the future).
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            type=int,
            default=7,
            help='Indicate the login time period in days starting from today'
        )
        parser.add_argument(
            '-r',
            '--dry',
            type=str,
            help='Indicate that the email should not be sent to author-support'
        )

    subject = 'Staff users CSV'
    to_addresses = ['author-support@edx.org']
    from_address = settings.DEFAULT_FROM_EMAIL
    txt_template_path = 'email/export_staff_users.txt'
    html_template_path = 'email/export_staff_users.html'
    csv_filename = 'staff_users.csv'

    def write_csv(self, query_set, filename):
        """
        Writes the queryset into a csv file with the given filename

        Arguments:
            query_set: query_set to be converted
            filename: filename for the csv
        """
        writer = csv.DictWriter(
            filename,
            fieldnames=['id', 'user__username', 'user__email', 'role']
        )
        writer.writeheader()
        for data_item in query_set:
            writer.writerow(data_item)

    def handle(self, *args, **kwargs):
        days = kwargs['days']
        dry = kwargs.get('dry')
        if dry:
            self.to_addresses = ['sustaining-mavericks@edx.org']
        current_date = datetime.now(tz=utc)
        starting_date = current_date - timedelta(days=days)
        active_courses = CourseOverview.objects.filter(end__gte=current_date).values_list('id', flat=True)
        course_access_roles = CourseAccessRole.objects.filter(
            role__in=['staff', 'instructor'],
            user__last_login__range=(starting_date, current_date),
            course_id__in=active_courses,
            user__is_staff=False
        ).values('id', 'user__username', 'user__email', 'role')
        if not course_access_roles:
            return
        with open(self.csv_filename, 'a+') as csv_file:
            self.write_csv(
                query_set=course_access_roles,
                filename=csv_file
            )
        context = {'time_period': days}
        try:
            self.send_email(context)
            logger.info(
                'Sent staff users email for the period {} to {}. Staff users count:{}'.format(
                    starting_date,
                    current_date,
                    course_access_roles.count()
                )
            )
        except Exception:
            logger.exception(
                'Failed to send staff users email for the period {}-{}'.format(starting_date, current_date)
            )

    def send_email(self, context):
        """
        Sends an email to admin containing a csv of all users who have logged in within the given days and
        have staff access role in active courses (Courses with end date in the future).

        Arguments:
            context: context for the email template
        """
        plain_content = self.render_template(self.txt_template_path, context)
        html_content = self.render_template(self.html_template_path, context)

        with open(self.csv_filename, 'r') as csv_file:
            email_message = EmailMultiAlternatives(self.subject, plain_content, self.from_address, to=self.to_addresses)
            email_message.attach_alternative(html_content, 'text/html')
            email_message.attach(self.csv_filename, csv_file.read(), 'text/csv')
            email_message.send()

        remove(self.csv_filename)

    def render_template(self, path, context):
        """
        Takes a template path and context and returns a rendered template

        Arguments:
            path: path of the file
            context: context for the template
        """
        txt_template = get_template(path)
        return txt_template.render(context)
