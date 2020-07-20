"""
Views to add features in courseware.
"""

from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from openedx.core.lib.api.view_utils import view_auth_classes

from .constants import COMP_ASSESS_RECORD_SUCCESS_MSG
from .helpers import get_competency_assessments_score, revert_user_attempts_from_edx, validate_problem_id
from .models import CompetencyAssessmentRecord
from .serializers import CompetencyAssessmentRecordSerializer


@api_view()
@view_auth_classes(is_authenticated=True)
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def competency_assessments_score_view(request, chapter_id):
    """
    API View to fetch competency assessments score.
    """
    try:
        score_dict = get_competency_assessments_score(request.user, chapter_id)
        return Response(score_dict, status=status.HTTP_200_OK)
    except (CourseAccessRedirect, CoursewareAccessException):
        return Response({
            'detail': _('User does not have access to this course'),
        }, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@view_auth_classes(is_authenticated=True)
def record_and_fetch_competency_assessment(request, chapter_id):
    """
    :param request:
    :param chapter_id:
    request's POST data must have following keys
        problem_id: UsageKeyField, block-v1:PUCIT+IT1+1+type@problem+block@7f1593ef300e4f569e26356b65d3b76b
        problem_text: String, This is a problem
        assessment_type: String, pre/post
        attempt: Integer, 1
        correctness: String, correct/incorrect
        choice_id: String, 1 or '0,1,2,3' in case of multiple selected choices
        choice_text: String, This is correct choice
        score:Integer, 1
    :return: JSON
    """
    competency_records = request.data

    serializer = CompetencyAssessmentRecordSerializer(data=competency_records, context=dict(request=request), many=True)
    if serializer.is_valid():
        serializer.save()
        competency_assessment_score = get_competency_assessments_score(request.user, chapter_id)
        return Response(
            {
                'competency_assessment_score': competency_assessment_score,
                'message': COMP_ASSESS_RECORD_SUCCESS_MSG
            }, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@view_auth_classes(is_authenticated=True)
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def revert_user_post_assessment_attempts(request, course_id):
    user = request.user
    problem_id = request.data.get('problem_id')
    validated_problem_id = validate_problem_id(problem_id)
    reverted_attempts_count = CompetencyAssessmentRecord.objects.revert_user_post_assessment_attempts(
                                problem_id=validated_problem_id, user=user)
    has_deleted_post_assessment_attempts = reverted_attempts_count > 0
    if has_deleted_post_assessment_attempts:
        revert_user_attempts_from_edx(course_id, user, validated_problem_id)
        success_response = {
            'message': _('Your attempts has been reverted successfully')
        }
        return Response(success_response, status=status.HTTP_200_OK)
    else:
        raise ValidationError(_('This user has no attempts for this problem id in post assessment'))
