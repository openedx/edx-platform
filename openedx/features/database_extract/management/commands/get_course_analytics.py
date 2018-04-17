import base64
import csv
import json
import tempfile

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


from courseware.models import StudentModule
from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import get_enrolled_students
from lms.djangoapps.onboarding.models import Organization
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey

from common.lib.mandrill_client.client import MandrillClient
from openedx.features.database_extract.models import TargetCourse


class Command(BaseCommand):
    help = 'Generates the analytics data for each course_id in targetcourse table'

    def handle(self, **options):
        target_courses = TargetCourse.objects.all()
        json_data = []

        for target_course in target_courses:
            user_profiles = get_enrolled_students(target_course.course_id)

            for profile in user_profiles:
                data = {
                    'student_id': profile.user.id,
                    'email': profile.user.email,
                    'first_name': profile.user.first_name,
                    'last_name': profile.user.last_name,
                    'date_joined': profile.user.date_joined.__str__(),
                    'bio': profile.bio,
                    'city': profile.city,
                    'country': profile.country.__str__(),
                    'language': profile.language,
                    'english_proficiency': profile.user.extended_profile.english_proficiency,
                    'label': profile.user.extended_profile.organization.label if
                    profile.user.extended_profile.organization else '',
                }
                json_data.append(data)
        with tempfile.TemporaryFile() as tmp:
            # Do stuff with tmp
            fieldnames = ['student_id', 'email', 'first_name', 'last_name',
                          'date_joined', 'bio', 'city', 'country', 'language',
                          'english_proficiency', 'label']
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            for row in json_data:
                writer.writerow(row)
            tmp.seek(0)
            MandrillClient().send_mail(
                template_name=MandrillClient.ACUMEN_DATA_TEMPLATE,
                user_email='osama.arshad@arbisoft.com',
                context={},
                attachments=[
                    {
                        "type": "text/plain",
                        "name": "data.csv",
                        "content": base64.encodestring(tmp.read())
                    }
                ]
            )

