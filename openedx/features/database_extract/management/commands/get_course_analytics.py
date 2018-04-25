import base64
import csv
import json
import tempfile
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from common.lib.mandrill_client.client import MandrillClient
from certificates.models import GeneratedCertificate
from courseware.models import StudentModule
from lms.djangoapps.grades.models import PersistentCourseGrade, PersistentSubsectionGrade
from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import get_enrolled_students
from lms.djangoapps.onboarding.models import Organization
from student.models import CourseEnrollment, AnonymousUserId, anonymous_id_for_user
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.teams.models import CourseTeamMembership, CourseTeam
from openassessment.data import OraAggregateData
from openassessment.fileupload import api as ora_file_upload_api
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.features.database_extract.models import TargetCourse
from submissions.models import StudentItem, Submission, Score
from submissions.api import _get_or_create_student_item


def get_file_url(answer):
    try:
        return ora_file_upload_api.get_download_url(answer.file_key)
    except:
        return ""


class Command(BaseCommand):
    help = 'Generates the analytics data for each course_id in targetcourse table'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, **options):
        target_courses = TargetCourse.objects.all()
        data = []

        for target_course in target_courses:
            course_data = {
                'course_structure': {},
                'team_data': [],
                'user_data': {
                    'demographic_data': {},
                    'performance_data': [],
                }
            }
            course_key = CourseKey.from_string(target_course.course_id)

            course_structure = CourseStructure.objects.get(course_id=course_key)
            course_teams = CourseTeam.objects.filter(course_id=course_key)

            course_data['course_structure'] = {
                'created': course_structure.created.__str__(),
                'modified': course_structure.modified.__str__(),
                'course_id': course_structure.course_id.to_deprecated_string(),
                'structure_json': course_structure.structure_json,
                'discussion_id_map_json': course_structure.discussion_id_map_json,
            }

            for team in course_teams:
                team_data = {
                    'team_id': course_team.team_id,
                    'discussion_topic_id': course_team.discussion_topic_id,
                    'name': course_team.name,
                    'course_id': course_team.course_id.to_deprecated_string(),
                    'topic_id': course_team.topic_id,
                    'date_created': course_team.date_created.__str__(),
                    'description': course_team.description,
                    'country': course_team.country,
                    'language': course_team.language,
                    'last_activity_at': course_team.last_activity_at.__str__(),
                    'team_size': course_team.team_size,
                }
                course_data['team_data'].push(team_data)

            user_profiles = get_enrolled_students(target_course.course_id)
            for profile in user_profiles:
                # get the user profie data from NodeBB API
                data_endpoint = settings.NODEBB_ENDPOINT + '/api/v2/users/data'
                headers = {'Authorization': 'Bearer ' + settings.NODEBB_MASTER_TOKEN}
                response = requests.post(data_endpoint,
                                         data={'_uid': 1, 'username': profile.user.username},
                                         headers=headers)

                user_community_data = json.loads(response._content)['payload']

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
                    'reputation': user_community_data['reputation'],
                    'postcount': user_community_data['postcount'],
                }

                anon_user_id = AnonymousUserId.objects.get(
                    user=profile.user,
                    course_id=course_key
                )

                perf_data = {
                    'team_memberships': [{
                        'team_id': membership.team_id,
                        'date_joined': membership.date_joined.__str__(),
                        'last_activity_at': membership.last_activity_at.__str__(),
                    } for membership in CourseTeamMembership.objects.filter(user_id=profile.user.id)],

                    'student_modules': [{
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

                    'persistent_course_grades': [{
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

                    'persistent_subsection_grades': [{
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

                    'generated_certificates': [{
                        'course_id': certificate.course_id.to_deprecated_string(),
                        'verify_uuid': certificate.verify_uuid,
                        'download_uuid': certificate.download_uuid,
                        'download_url': certificate.download_url,
                        'grade': certificate.grade,
                        'key': certificate.key,
                        'distinction': certificate.distinction,
                        'status': certificate.status,
                        'mode': certificate.mode,
                        'name': certificate.name,
                        'created_date': certificate.created_date.__str__(),
                        'modified_date': certificate.modified_date.__str__(),
                        'error_reason': certificate.error_reason,
                    } for certificate in GeneratedCertificate.objects.filter(user_id=profile.user.id)],

                    'submissions': {
                        'studentitems': [{
                            'course_id': item.course_id,
                            'item_id': item.item_id,
                            'item_type': item.item_type,
                        } for item in StudentItem.objects.filter(student_id=anon_user_id.anonymous_user_id)],

                        'submissions': [{
                            'uuid': submission.uuid,
                            'attempt_number': submission.attempt_number,
                            'submitted_at': submission.submitted_at.__str__(),
                            'created_at': submission.created_at.__str__(),
                            'answer': submission.answer,
                            'file_url': get_file_url(submission.answer),
                            'student_item_id': submission.student_item_id,
                            'status': submission.status,
                        } for submission in Submission.objects.filter(
                            student_item__student_id=anon_user_id.anonymous_user_id
                        )],

                        'scores': [{
                            'points_earned': score.points_earned,
                            'points_possible': score.points_possible,
                            'created_at': score.created_at.__str__(),
                            'reset': score.reset,
                            'student_item_id': score.student_item_id,
                            'submission_id': score.submission_id,
                        } for score in Score.objects.filter(student_item__student_id=anon_user_id.anonymous_user_id)],
                    }

                }
                course_data['user_data']['demographic_data'] = demo_data
                course_data['user_data']['performance_data'] = perf_data

            data.append(course_data)

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
