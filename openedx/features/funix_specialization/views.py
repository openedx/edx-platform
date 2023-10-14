
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from cms.djangoapps.contentstore.views.certificates import _get_course_and_check_access
from common.djangoapps.util.json_request import JsonResponse
from opaque_keys.edx.keys import  CourseKey
from rest_framework.decorators import api_view
from django.shortcuts import redirect
from openedx.features.funix_specialization.models import FunixSpecialization, FunixSpecializationCourse

@login_required
@ensure_csrf_cookie
def funix_specialization_view (request, course_id):
    course_key = CourseKey.from_string(course_id)
    try:
        course = _get_course_and_check_access(course_key, request.user)
    except PermissionDenied:
        msg = _('PermissionDenied: Failed in authenticating {user}').format(user=request.user)
        return JsonResponse({"error": msg}, status=403)
    listSpec = FunixSpecialization.getAllSpec()
    specCourse = FunixSpecializationCourse.getSpecializationCourse(course_id = course_id)

    
    context = {
        "context_course" : course ,
        "all_spec" : listSpec,
        'list_spec_course' : specCourse
    }
    
    return render_to_response('funix_specialization.html' , context)




def setting_specialization(request):
    user = request.user
    if request.method == 'POST':
        spec_name = request.POST.get('spec_name')
        course_id = request.POST.get('course_id')
        spec_id = request.POST.get('specialization-select')
     
        if spec_name :
            FunixSpecialization.create_specialization_funix(spec_name=spec_name, user_id=user.id)
        if spec_id :
            FunixSpecializationCourse.setSpecializationCourseFunix(course_id=course_id, spec_id=spec_id, user_id=user.id )
        
        
   
        return redirect('funix_specialization', course_id =course_id)


@api_view(['POST'])
@login_required
@ensure_csrf_cookie
def remove_specialization (request):
    if request.method == 'POST':
        course_id = request.data.get('course_id')
        spec_id  = request.data.get('spec_id')
        FunixSpecializationCourse.removeSpecializationCourseFunix(course_id=course_id, spec_id=spec_id)
        
    
    return redirect('funix_specialization', course_id =course_id)