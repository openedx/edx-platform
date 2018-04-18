import base64
import csv
import json
import tempfile

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


from courseware.models import StudentModule
from lms.djangoapps.grades.models import PersistentCourseGrade, PersistentSubsectionGrade
from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import get_enrolled_students
from lms.djangoapps.onboarding.models import Organization
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.teams.models import CourseTeamMembership
from common.lib.mandrill_client.client import MandrillClient
from openedx.features.database_extract.models import TargetCourse


class Command(BaseCommand):
    help = 'Generates the analytics data for each course_id in targetcourse table'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, **options):
        target_courses = TargetCourse.objects.all()
        data = []

        for target_course in target_courses:
            user_profiles = get_enrolled_students(target_course.course_id)

            for profile in user_profiles:
                demo_data = {
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

                perf_data = {
                    'team_membership': [{
                        'team_id': membership.team_id,
                        'date_joined': membership.date_joined.__str__(),
                        'last_activity_at': membership.last_activity_at.__str__(),
                    } for membership in CourseTeamMembership.objects.filter(user_id=profile.user.id)][0],

                    'studentmodules': [{
                        'module_type': module.module_type,
                        'module_id': module.module_state_key.to_deprecated_string(),
                        'course_id': module.course_id.to_deprecated_string(),
                        'state': module.state,
                        'grade': module.grade,
                        'max_grade': module.max_grade,
                        'done': module.done,
                        'created': module.created.__str__(),
                        'modified': module.modified.__str__(),
                    } for module in StudentModule.objects.filter(student_id=profile.user.id)],

                    'persistentcoursegrade': [{
                        'created': course_grade.created.__str__(),
                        'modified': course_grade.modified.__str__(),
                        'course_id': course_grade.course_id.to_deprecated_string(),
                        'course_edited_timestamp': course_grade.course_edited_timestamp.__str__(),
                        'course_version': course_grade.course_version,
                        'grading_policy_hash': course_grade.grading_policy_hash,
                        'percent_grade': course_grade.percent_grade,
                        'letter_grade': course_grade.letter_grade,
                        'passed_timestamp': course_grade.passed_timestamp.__str__(),
                    } for course_grade in PersistentCourseGrade.objects.filter(user_id=profile.user.id)],

                    'persistentsubsectiongrade': [{
                        'created': subsection_grade.created.__str__(),
                        'modified': subsection_grade.modified.__str__(),
                        'course_id': subsection_grade.course_id.to_deprecated_string(),
                        'usage_key': subsection_grade.full_usage_key.to_deprecated_string(),
                        'subtree_edited_timestamp': subsection_grade.subtree_edited_timestamp.__str__(),
                        'course_version': subsection_grade.course_version,
                        'earned_all': subsection_grade.earned_all,
                        'possible_all': subsection_grade.possible_all,
                        'earned_graded': subsection_grade.earned_graded,
                        'possible_graded': subsection_grade.possible_graded,
                        'visible_blocks': subsection_grade.visible_blocks.blocks_json,
                        'first_attempted': subsection_grade.first_attempted.__str__(),
                    } for subsection_grade in PersistentSubsectionGrade.objects.filter(user_id=profile.user.id)],
                }
                data.append({
                    'demo_data': demo_data,
                    'perf_data': perf_data,
                })
        with tempfile.TemporaryFile() as tmp:
            MandrillClient().send_mail(
                template_name=MandrillClient.ACUMEN_DATA_TEMPLATE,
                user_email=options['email'],
                context={},
                attachments=[
                    {
                        "type": "text/plain",
                        "name": "data.json",
                        "content": base64.encodestring(json.dumps(data))
                    }
                ]
            )
