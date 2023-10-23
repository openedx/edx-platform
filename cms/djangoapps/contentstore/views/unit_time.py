from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie 
from common.djangoapps.util.json_request import JsonResponse
from openedx.core.djangoapps.content.course_overviews.models import CourseUnitTime
from .helpers import usage_key_with_run
from .item import _get_xblock

@api_view(['GET'])
@login_required
@ensure_csrf_cookie
def get_time_course_unit (request, block_id):
    # usage_key = usage_key_with_run(block_id)
  
    # block = _get_xblock(usage_key=usage_key, user=request.user)
    # for a in block.children :
    #     print('==============', str(a))
    unit_time = CourseUnitTime.get_unit_time(block_id=block_id)
    
    if unit_time is not None :
        data = {
        "id" : block_id,
        "total" : unit_time.total,
        "title" : unit_time.display_name,
 
    }
    else : 
        data = {
            "id" : block_id,
            "total" : "" ,

        }

    return JsonResponse(data) 


@api_view(['POST'])
@login_required
@ensure_csrf_cookie
def set_course_time_unit (request) :
    
    if request.method == 'POST' :
        total = request.data.get('total')
        sequence_id = request.data.get('suquence_id')
        course_id = request.data.get('courseId')
        display_name = request.data.get('title')
       
        CourseUnitTime.set_unit_time(block_id=sequence_id, total = total, course_id=course_id, display_name=display_name)
    return JsonResponse({'a':'a'})