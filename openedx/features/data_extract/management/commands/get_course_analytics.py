import base64
import json
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
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
            for profile in user_profiles:
                demo_data = get_user_demographic_data(profile)
                progress_data = get_user_progress_data(course_key, profile)

                course_data['user_data'].append({
                    'demographic_data': demo_data,
                    'progress_data': progress_data,
                })

            with tempfile.TemporaryFile() as tmp:
                for email in emails:
                    MandrillClient().send_mail(
                        template_name=MandrillClient.ACUMEN_DATA_TEMPLATE,
                        user_email=email,
                        context={},
                        attachments=[
                            {
                                "type": "text/plain",
                                "name": "data.json",
                                "content": base64.encodestring(json.dumps(course_data))
                            }
                        ]
                    )
