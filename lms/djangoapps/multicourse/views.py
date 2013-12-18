from django.conf import settings
from edxmako.shortcuts import render_to_response

from multicourse import multicourse_settings


def edxhome(request):
    ''' Home page (link from main header). List of courses.  '''
    if settings.DEBUG:
        print "[djangoapps.multicourse.edxhome] EDX_ROOT_URL = " + settings.EDX_ROOT_URL
    if settings.ENABLE_MULTICOURSE:
        context = {'courseinfo': multicourse_settings.COURSE_SETTINGS}
        return render_to_response("edXhome.html", context)
    return info(request)
