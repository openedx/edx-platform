import requests
import json

from django.conf import settings

from certificates.models import GeneratedCertificate
from courseware.models import StudentModule
from lms.djangoapps.grades.models import PersistentCourseGrade, PersistentSubsectionGrade
from lms.djangoapps.onboarding.models import Organization
from lms.djangoapps.teams.models import CourseTeamMembership, CourseTeam
from student.models import AnonymousUserId
from lms.djangoapps.teams.models import CourseTeamMembership, CourseTeam
from openassessment.fileupload import api as ora_file_upload_api
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from submissions.models import StudentItem, Submission, Score


def get_file_url(answer):
    """
    returns the signed URL of the file
    """
    if answer.get('file_key'):
        return ora_file_upload_api.get_download_url(answer['file_key'])
    return None


def get_course_structure(course_key):
    """
    Returns data about the course structure to course_data dict

    Arguments:
    course_key (CourseKey): CourseKey object for specified course
    """
    course_structure = CourseStructure.objects.get(course_id=course_key)

    return {
        'created': course_structure.created.__str__(),
        'modified': course_structure.modified.__str__(),
        'course_id': course_structure.course_id.to_deprecated_string(),
        'structure_json': course_structure.structure_json,
        'discussion_id_map_json': course_structure.discussion_id_map_json,
    }


def get_teams_data(course_key):
    """
    Returns data about all the teams in a course

    Arguments:
    course_key (CourseKey): CourseKey object for specified course
    """
    course_teams = CourseTeam.objects.filter(course_id=course_key)
    team_data = []
    for team in course_teams:
        team_data.append({
            'team_id': team.team_id,
            'name': team.name,
            'course_id': team.course_id.to_deprecated_string(),
            'topic_id': team.topic_id,
            'date_created': team.date_created.__str__(),
            'description': team.description,
            'country': team.country.__str__(),
            'language': team.language,
            'last_activity_at': team.last_activity_at.__str__(),
            'team_size': team.team_size,
        })
    return team_data


def get_user_demographic_data(profile):
    """
    Returns the demographic data for a single user

    Arguments:
    profile (UserProfile): UserProfile object for the learner
    """
    # get the user community profile data from NodeBB API
    data_endpoint = settings.NODEBB_ENDPOINT + '/api/v2/users/data'
    headers = {'Authorization': 'Bearer ' + settings.NODEBB_MASTER_TOKEN}
    response = requests.post(data_endpoint,
                             data={'_uid': 1, 'username': profile.user.username},
                             headers=headers)

    user_community_data = json.loads(response._content)['payload']
    reputation = user_community_data.get('reputation', 0)
    postcount = user_community_data.get('postcount', 0)

    return {
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
        'organization_label': profile.user.extended_profile.organization.label if
        profile.user.extended_profile.organization else '',
        'reputation': reputation,
        'postcount': postcount,
    }


def get_user_progress_data(course_key, profile, anonymous_user_id):
    """
    Returns all the data regarding the progress the user has made in a course

    Arguments:
    course_key (CourseKey): CourseKey object for specified course
    profile (UserProfile): UserProfile object for the learner
    """

    return {
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
        } for module in StudentModule.objects.filter(student_id=profile.user.id, course_id=course_key)],

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
        } for course_grade in PersistentCourseGrade.objects.filter(user_id=profile.user.id, course_id=course_key)],

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
        } for subsection_grade in PersistentSubsectionGrade.objects.filter(
            user_id=profile.user.id,
            course_id=course_key
        )],

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
        } for certificate in GeneratedCertificate.objects.filter(user_id=profile.user.id, course_id=course_key)],

        'course_submission_data': {
            'student_items': [{
                'id': item.id,
                'student_id': item.student_id,
                'course_id': item.course_id,
                'item_id': item.item_id,
                'item_type': item.item_type,
            } for item in StudentItem.objects.filter(
                student_id=anonymous_user_id,
                course_id=course_key.to_deprecated_string()
            )],

            'submissions': [{
                'id': submission.id,
                'uuid': submission.uuid,
                'attempt_number': submission.attempt_number,
                'submitted_at': submission.submitted_at.__str__(),
                'created_at': submission.created_at.__str__(),
                'answer': submission.answer,
                'answer_file_url': get_file_url(submission.answer),
                'student_item_id': submission.student_item_id,
                'status': submission.status,
            } for submission in Submission.objects.filter(
                student_item__student_id=anonymous_user_id,
                student_item__course_id=course_key.to_deprecated_string()
            )],

            'student_scores': [{
                'id': score.id,
                'points_earned': score.points_earned,
                'points_possible': score.points_possible,
                'created_at': score.created_at.__str__(),
                'reset': score.reset,
                'student_item_id': score.student_item_id,
                'submission_id': score.submission_id,
            } for score in Score.objects.filter(
                student_item__student_id=anonymous_user_id,
                student_item__course_id=course_key.to_deprecated_string()
            )],
        }
    }
