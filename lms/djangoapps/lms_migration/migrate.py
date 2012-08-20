#
# migration tools for content team to go from stable-edx4edx to LMS+CMS
#

import logging
from pprint import pprint
import xmodule.modulestore.django as xmodule_django
from xmodule.modulestore.django import modulestore

from django.http import HttpResponse
from django.conf import settings

log = logging.getLogger("mitx.lms_migrate")
LOCAL_DEBUG = True
ALLOWED_IPS = settings.LMS_MIGRATION_ALLOWED_IPS

def escape(s):
    """escape HTML special characters in string"""
    return str(s).replace('<','&lt;').replace('>','&gt;')

def manage_modulestores(request,reload_dir=None):
    '''
    Manage the static in-memory modulestores.

    If reload_dir is not None, then instruct the xml loader to reload that course directory.
    '''
    html = "<html><body>"

    def_ms = modulestore()
    courses = def_ms.get_courses()

    #----------------------------------------
    # check on IP address of requester

    ip = request.META.get('HTTP_X_REAL_IP','')	# nginx reverse proxy
    if not ip:
        ip = request.META.get('REMOTE_ADDR','None')

    if LOCAL_DEBUG:
        html += '<h3>IP address: %s ' % ip
        html += '<h3>User: %s ' % request.user
        log.debug('request from ip=%s, user=%s' % (ip,request.user))

    if not (ip in ALLOWED_IPS or 'any' in ALLOWED_IPS):
        if request.user and request.user.is_staff:
            log.debug('request allowed because user=%s is staff' % request.user)
        else:
            html += 'Permission denied'
            html += "</body></html>"
            log.debug('request denied, ALLOWED_IPS=%s' % ALLOWED_IPS)
            return HttpResponse(html)

    #----------------------------------------
    # reload course if specified

    if reload_dir is not None:
        if reload_dir not in def_ms.courses:
            html += "<h2><font color='red'>Error: '%s' is not a valid course directory</font></h2>" % reload_dir
        else:
            html += "<h2><font color='blue'>Reloaded course directory '%s'</font></h2>" % reload_dir
            def_ms.try_load_course(reload_dir)

    #----------------------------------------

    html += '<h2>Courses loaded in the modulestore</h2>'
    html += '<ol>'
    for cdir, course in def_ms.courses.items():
        html += '<li><a href="%s/migrate/reload/%s">%s</a> (%s)</li>' % (settings.MITX_ROOT_URL,
                                                            escape(cdir),
                                                            escape(cdir),
                                                            course.location.url())
    html += '</ol>'

    #----------------------------------------

    dumpfields = ['definition','location','metadata']

    for cdir, course in def_ms.courses.items():
        html += '<hr width="100%"/>'
        html += '<h2>Course: %s (%s)</h2>' % (course.display_name,cdir)

        for field in dumpfields:
            data = getattr(course,field)
            html += '<h3>%s</h3>' % field
            if type(data)==dict:
                html += '<ul>'
                for k,v in data.items():
                    html += '<li>%s:%s</li>' % (escape(k),escape(v))
                html += '</ul>'
            else:
                html += '<ul><li>%s</li></ul>' % escape(data)


    #----------------------------------------

    html += '<hr width="100%"/>'
    html += "courses: <pre>%s</pre>" % escape(courses)

    ms = xmodule_django._MODULESTORES
    html += "modules: <pre>%s</pre>" % escape(ms)
    html += "default modulestore: <pre>%s</pre>" % escape(unicode(def_ms))

    #----------------------------------------

    log.debug('_MODULESTORES=%s' % ms)
    log.debug('courses=%s' % courses)
    log.debug('def_ms=%s' % unicode(def_ms))

    html += "</body></html>"
    return HttpResponse(html)
