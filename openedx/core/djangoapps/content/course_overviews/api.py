"""
CourseOverview api
"""
import logging

from django.http.response import Http404
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie 
from common.djangoapps.util.json_request import JsonResponse

from openedx.core.djangoapps.catalog.api import get_course_run_details
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, CourseOverviewSubText
from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)

log = logging.getLogger(__name__)


def get_course_overview_or_none(course_id):
    """
    Retrieve and return course overview data for the provided course id.

    If the course overview does not exist, return None.
    """
    try:
        return CourseOverview.get_from_id(course_id)
    except CourseOverview.DoesNotExist:
        log.warning(f"Course overview does not exist for {course_id}")
        return None


def get_course_overview_or_404(course_id):
    """
    Retrieve and return course overview data for the provided course id.

    If the course overview does not exist, raises Http404.
    """
    try:
        return CourseOverview.get_from_id(course_id)
    except CourseOverview.DoesNotExist as e:
        raise Http404(f"Course overview does not exist for {course_id}") from e


def get_pseudo_course_overview(course_id):
    """
    Returns a pseudo course overview object for a deleted course.

    Params:
        course_id (CourseKey): The identifier for the course.
    Returns:
        (Temporary) CourseOverview object representing for a deleted course.
    """
    fields = ['title']
    course_run = get_course_run_details(course_id, fields)

    return CourseOverview(
        display_name=course_run.get('title'),
        display_org_with_default=course_id.org,
        certificates_show_before_end=True
    )


def get_course_overviews_from_ids(course_ids):
    """
    Return course overviews for the specified course ids.

    Params:
        course_ids (iterable[CourseKey])

    Returns:
        dict[CourseKey, CourseOverview|None]
    """
    return CourseOverview.get_from_ids(course_ids)


def get_course_overviews(course_ids):
    """
    Return (serialized) course_overview data for a given list of opaque_key course_ids.
    """
    overviews = CourseOverview.objects.filter(id__in=course_ids)
    return CourseOverviewBaseSerializer(overviews, many=True).data


# courseOverview_subtext

@api_view(['GET'])
@login_required
@ensure_csrf_cookie
def get_course_subtext (request,sequence_id) :

    sequenceSubText = CourseOverviewSubText.sequenceSubText(sequence_id)

    if sequenceSubText is not None :
        data = {
        "id" : sequence_id,
        "sub_text" : sequenceSubText.sub_text,
        "title" : sequenceSubText.title,
 
    }
    else : 
        data = {
            "id" : sequence_id,
            "sub_text" : "" ,

        }
    

    return JsonResponse(data)


@api_view(['POST'])
@login_required
@ensure_csrf_cookie
def set_course_subtext (request) :
    
    if request.method == 'POST' :
        sub_text = request.data.get('subtext')
        sequence_id = request.data.get('suquence_id')
        course_id = request.data.get('courseId')
        title = request.data.get('title')
       
        CourseOverviewSubText.setSubTextSequence(sequence_id=sequence_id, sub_text=sub_text, course_id=course_id ,title=title)
    return JsonResponse({'a':'a'})