from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response
from django.conf import settings

@login_required
def index(request, course_id=None, page=0): 
    course = settings.COURSES_BY_ID[course_id]
    return render_to_response('staticbook.html',{'page':int(page), 'course': course})

def index_shifted(request, page):
    return index(request, int(page)+24)
