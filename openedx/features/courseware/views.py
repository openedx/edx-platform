"""
Views to add features in courseware.
"""

from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from openedx.core.lib.api.view_utils import view_auth_classes

from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException

from .helpers import get_pre_post_assessments_score


@api_view()
@view_auth_classes(is_authenticated=True)
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def pre_post_assessments_score_view(request, course_id, chapter_id):
    """
    API View to fetch pre and post assessments score.
    """
    try:
        score_dict = get_pre_post_assessments_score(request.user, course_id, chapter_id)
        return Response(score_dict, status=status.HTTP_200_OK)
    except (CourseAccessRedirect, CoursewareAccessException):
        return Response({
                'detail': _('User does not have access to this course'),
                }, status=status.HTTP_403_FORBIDDEN)
