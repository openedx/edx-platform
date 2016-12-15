#
# migration tools for content team to go from stable-edx4edx to LMS+CMS
#

import json
import logging
import os
import xmodule.modulestore.django as xmodule_django
from xmodule.modulestore.django import modulestore

from django.http import HttpResponse
from django.conf import settings
import track.views

try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    from django.contrib.csrf.middleware import csrf_exempt

log = logging.getLogger("edx.lms_migrate")
LOCAL_DEBUG = True
ALLOWED_IPS = settings.LMS_MIGRATION_ALLOWED_IPS


def escape(s):
    """escape HTML special characters in string"""
    return str(s).replace('<', '&lt;').replace('>', '&gt;')


def getip(request):
    '''
    Extract IP address of requester from header, even if behind proxy
    '''
    ip = request.META.get('HTTP_X_REAL_IP', '')  	# nginx reverse proxy
    if not ip:
        ip = request.META.get('REMOTE_ADDR', 'None')
    return ip


def get_commit_id(course):
    #return course.metadata.get('GIT_COMMIT_ID', 'No commit id')
    return getattr(course, 'GIT_COMMIT_ID', 'No commit id')
    # getattr(def_ms.courses[reload_dir], 'GIT_COMMIT_ID','No commit id')


def set_commit_id(course, commit_id):
    #course.metadata['GIT_COMMIT_ID'] = commit_id
    course.GIT_COMMIT_ID = commit_id
    # def_ms.courses[reload_dir].GIT_COMMIT_ID = new_commit_id


def manage_modulestores(request, reload_dir=None, commit_id=None):
    '''
    Manage the static in-memory modulestores.

    If reload_dir is not None, then instruct the xml loader to reload that course directory.
    '''
    html = "<html><body>"

    def_ms = modulestore()
    courses = def_ms.get_courses()

    #----------------------------------------
    # check on IP address of requester

    ip = getip(request)

    if LOCAL_DEBUG:
        html += '<h3>IP address: %s <h3>' % ip
        html += '<h3>User: %s </h3>' % request.user
        html += '<h3>My pid: %s</h3>' % os.getpid()
        log.debug(u'request from ip=%s, user=%s', ip, request.user)

    if not (ip in ALLOWED_IPS or 'any' in ALLOWED_IPS):
        if request.user and request.user.is_staff:
            log.debug(u'request allowed because user=%s is staff', request.user)
        else:
            html += 'Permission denied'
            html += "</body></html>"
            log.debug('request denied, ALLOWED_IPS=%s', ALLOWED_IPS)
            return HttpResponse(html, status=403)

    #----------------------------------------
    # reload course if specified; handle optional commit_id

    if reload_dir is not None:
        if reload_dir not in def_ms.courses:
            html += '<h2 class="inline-error">Error: "%s" is not a valid course directory</h2>' % reload_dir
        else:
            # reloading based on commit_id is needed when running mutiple worker threads,
            # so that a given thread doesn't reload the same commit multiple times
            current_commit_id = get_commit_id(def_ms.courses[reload_dir])
            log.debug('commit_id="%s"', commit_id)
            log.debug('current_commit_id="%s"', current_commit_id)

            if (commit_id is not None) and (commit_id == current_commit_id):
                html += "<h2>Already at commit id %s for %s</h2>" % (commit_id, reload_dir)
                track.views.server_track(request,
                                         'reload %s skipped already at %s (pid=%s)' % (reload_dir,
                                                                                       commit_id,
                                                                                       os.getpid(),
                                                                                       ),
                                         {}, page='migrate')
            else:
                html += '<h2>Reloaded course directory "%s"</h2>' % reload_dir
                def_ms.try_load_course(reload_dir)
                gdir = settings.DATA_DIR / reload_dir
                new_commit_id = os.popen('cd %s; git log -n 1 | head -1' % gdir).read().strip().split(' ')[1]
                set_commit_id(def_ms.courses[reload_dir], new_commit_id)
                html += '<p>commit_id=%s</p>' % new_commit_id
                track.views.server_track(request, 'reloaded %s now at %s (pid=%s)' % (reload_dir,
                                                                                      new_commit_id,
                                                                                      os.getpid()), {}, page='migrate')

    #----------------------------------------

    html += '<h2>Courses loaded in the modulestore</h2>'
    html += '<ol>'
    for cdir, course in def_ms.courses.items():
        html += '<li><a href="%s/migrate/reload/%s">%s</a> (%s)</li>' % (
            settings.EDX_ROOT_URL,
            escape(cdir),
            escape(cdir),
            course.location.to_deprecated_string()
        )
    html += '</ol>'

    #----------------------------------------

    #dumpfields = ['definition', 'location', 'metadata']
    dumpfields = ['location', 'metadata']

    for cdir, course in def_ms.courses.items():
        html += '<hr width="100%"/>'
        html += '<h2>Course: %s (%s)</h2>' % (course.display_name_with_default_escaped, cdir)

        html += '<p>commit_id=%s</p>' % get_commit_id(course)

        for field in dumpfields:
            data = getattr(course, field, None)
            html += '<h3>%s</h3>' % field
            if isinstance(data, dict):
                html += '<ul>'
                for k, v in data.items():
                    html += '<li>%s:%s</li>' % (escape(k), escape(v))
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

    log.debug('_MODULESTORES=%s', ms)
    log.debug('courses=%s', courses)
    log.debug('def_ms=%s', unicode(def_ms))

    html += "</body></html>"
    return HttpResponse(html)


@csrf_exempt
def gitreload(request, reload_dir=None):
    '''
    This can be used as a github WebHook Service Hook, for reloading of the content repo used by the LMS.

    If reload_dir is not None, then instruct the xml loader to reload that course directory.
    '''
    html = "<html><body>"
    ip = getip(request)

    html += '<h3>IP address: %s ' % ip
    html += '<h3>User: %s ' % request.user

    ALLOWED_IPS = []  	# allow none by default
    if hasattr(settings, 'ALLOWED_GITRELOAD_IPS'):  	# allow override in settings
        ALLOWED_IPS = settings.ALLOWED_GITRELOAD_IPS

    if not (ip in ALLOWED_IPS or 'any' in ALLOWED_IPS):
        if request.user and request.user.is_staff:
            log.debug(u'request allowed because user=%s is staff', request.user)
        else:
            html += 'Permission denied'
            html += "</body></html>"
            log.debug('request denied from %s, ALLOWED_IPS=%s', ip, ALLOWED_IPS)
            return HttpResponse(html)

    #----------------------------------------
    # see if request is from github (POST with JSON)

    if reload_dir is None and 'payload' in request.POST:
        payload = request.POST['payload']
        log.debug("payload=%s", payload)
        gitargs = json.loads(payload)
        log.debug("gitargs=%s", gitargs)
        reload_dir = gitargs['repository']['name']
        log.debug("github reload_dir=%s", reload_dir)
        gdir = settings.DATA_DIR / reload_dir
        if not os.path.exists(gdir):
            log.debug("====> ERROR in gitreload - no such directory %s", reload_dir)
            return HttpResponse('Error')
        cmd = "cd %s; git reset --hard HEAD; git clean -f -d; git pull origin; chmod g+w course.xml" % gdir
        log.debug(os.popen(cmd).read())
        if hasattr(settings, 'GITRELOAD_HOOK'):  	# hit this hook after reload, if set
            gh = settings.GITRELOAD_HOOK
            if gh:
                ghurl = '%s/%s' % (gh, reload_dir)
                r = requests.get(ghurl)
                log.debug("GITRELOAD_HOOK to %s: %s", ghurl, r.text)

    #----------------------------------------
    # reload course if specified

    if reload_dir is not None:
        def_ms = modulestore()
        if reload_dir not in def_ms.courses:
            html += '<h2 class="inline-error">Error: "%s" is not a valid course directory</font></h2>' % reload_dir
        else:
            html += "<h2>Reloaded course directory '%s'</h2>" % reload_dir
            def_ms.try_load_course(reload_dir)
            track.views.server_track(request, 'reloaded %s' % reload_dir, {}, page='migrate')

    return HttpResponse(html)
