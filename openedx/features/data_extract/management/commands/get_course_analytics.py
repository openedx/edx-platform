import base64
import json
import tempfile
import pyminizip

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError

from common.lib.mandrill_client.client import MandrillClient
from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import get_enrolled_students
from opaque_keys.edx.keys import CourseKey
from openedx.features.data_extract.models import CourseDataExtraction

from openedx.features.data_extract.helpers import (
    get_course_structure,
    get_teams_data,
    get_user_demographic_data,
    get_user_progress_data,
)
from student.models import AnonymousUserId


class Command(BaseCommand):
    help = 'Generates the analytics data for each course_id in coursedataextraction table'

    def handle(self, **options):
        target_courses = CourseDataExtraction.objects.all()

        for target_course in target_courses:
            emails = map(unicode.strip, target_course.emails.split(','))
            course_key = CourseKey.from_string(target_course.course_id)

            course_data = {
                'course_structure': get_course_structure(course_key),
                'team_data': get_teams_data(course_key),
                'user_data': []
            }

            user_profiles = get_enrolled_students(target_course.course_id)
            anon_user_ids = dict(list(map(lambda x: (x.user.username, x.anonymous_user_id,),
                                          AnonymousUserId.objects.filter(course_id=course_key))))

            for profile in user_profiles:
                demographic_data = get_user_demographic_data(profile)
                progress_data = get_user_progress_data(course_key, profile, anon_user_ids[profile.user.username])

                course_data['user_data'].append({
                    'demographic_data': demographic_data,
                    'progress_data': progress_data,
                })

            with tempfile.NamedTemporaryFile() as tmp:
                pyminizip.compress(tmp.name, '/tmp/data.zip', 'philu2miriam', 1)
                for email in emails:
                    email_message = EmailMessage(
                        subject='Data from PhilU',
                        body='hello there',
                        from_email='no-reply@philanthropyu.org',
                        to=[email]
                    )
                    email_message.attach_file('/tmp/data.zip')
                    email_message.send()
