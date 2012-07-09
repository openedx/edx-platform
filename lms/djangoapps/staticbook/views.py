from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor

@login_required
def index(request, course_id=None, page=0): 
    course_location = CourseDescriptor.id_to_location(course_id)
    course = modulestore().get_item(course_location)
    return render_to_response('staticbook.html',{'page':int(page), 'course': course})

def index_shifted(request, page):
    return index(request, int(page)+24)
