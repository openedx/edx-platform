"""
Views to add features in courseware.
"""

from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import CourseKey, UsageKey
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from submissions.api import SubmissionError

from courseware.models import StudentModule
from lms.djangoapps.instructor.enrollment import reset_student_attempts
from openedx.core.lib.api.view_utils import view_auth_classes

from .helpers import validate_problem_id
from .models import CompetencyAssessmentRecord
from .serializers import CompetencyAssessmentRecordSerializer


@view_auth_classes(is_authenticated=True)
class CompetencyAssessmentAPIView(APIView):
    """Competency assessment APIs to save user attempts and get assessment scores"""

    def get(self, request, chapter_id):
        """Return assessment score"""
        return self._get_score_response(chapter_id)

    def post(self, request, chapter_id):
        """Save list of competency assessment records and return assessment score or errors"""
        competency_records = request.data
        serializer = CompetencyAssessmentRecordSerializer(data=competency_records, many=True, context={
            'request': request
        })
        if serializer.is_valid():
            serializer.save()
            return self._get_score_response(chapter_id, status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_score_response(self, chapter_id, status=status.HTTP_200_OK):
        score = CompetencyAssessmentRecord.objects.get_score(self.request.user, chapter_id)
        return Response(score, status=status)


@view_auth_classes(is_authenticated=True)
class RevertPostAssessmentAttemptsAPIView(APIView):
    """Revert user post assessment attempts API"""

    def post(self, request, course_id):
        user = request.user
        problem_id = request.data.get('problem_id')
        validated_problem_id = validate_problem_id(problem_id)
        reverted_attempts_count = CompetencyAssessmentRecord.objects.revert_user_post_assessment_attempts(
            problem_id=validated_problem_id, user=user
        )
        has_deleted_post_assessment_attempts = reverted_attempts_count > 0
        if has_deleted_post_assessment_attempts:
            self._revert_user_attempts_from_edx(course_id, validated_problem_id)

        return Response(status=status.HTTP_200_OK)

    def _revert_user_attempts_from_edx(self, course_id, problem_usage_key):
        """
        :param course_id: str course id
        :param problem_usage_key: UsageKey problem id
        """
        try:
            user = self.request.user
            course_id = CourseKey.from_string(course_id)
            module_state_key = problem_usage_key.map_into_course(course_id)
            reset_student_attempts(
                course_id=course_id,
                student=user,
                module_state_key=module_state_key,
                requesting_user=user,
                delete_module=True
            )
        except InvalidKeyError:
            raise ValidationError(_('Course id is not valid.'))
        except StudentModule.DoesNotExist:
            raise ValidationError(_('Module does not exist.'))
        except SubmissionError:
            # Trust the submissions API to log the error
            raise APIException(_('An error occurred while deleting the score.'))
