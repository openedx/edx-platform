import csv
import json
import logging
import os
import string
import subprocess
import time

from random import choice
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from student.models import CourseEnrollment
from student.models import UserProfile, Registration
from external_auth.models import ExternalAuthMap
from external_auth.views import generate_password

from courseware.access import get_access_group_name
from courseware.courses import get_course_by_id

from django.contrib.auth import authenticate
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils.html import escape
from django.contrib.admin.views.decorators import staff_member_required
from mitxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.store_utilities import delete_course

import track.views

log = logging.getLogger(__name__)

def git_info_for_course(cdir):
    gdir = settings.DATA_DIR / cdir
    info = [gdir, '', '']
    if os.path.exists(gdir):
        cmd = 'cd {0}; git log -1'.format(gdir)
        for k in os.popen(cmd).readlines():
            if 'commit' in k:
                info[0] = k.split()[1]
            elif 'Author' in k:
                info[2] = k.split()[1]
            elif 'Date' in k:
                info[1] = k.split(' ', 1)[1].strip()
    return info

def get_course_from_git(gitloc, is_using_mongo, def_ms, datatable):
    msg = ''
    if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
       gitloc.startswith('https:') or gitloc.startswith('git:')):
        msg += \
            _("The git repo location should end with '.git', and be for SSH access")
        return msg

    if is_using_mongo:
        acscript = getattr(settings, 'CMS_ADD_COURSE_SCRIPT', '')
        if not acscript or not os.path.exists(acscript):
            msg = "<font color='red'>{0}</font>".format(_('Must configure CMS_ADD_COURSE_SCRIPT in settings first!'))
            return msg
        
        # Attempt to use the same cms settings as we have in lms (cms has import, and lms does not)
        bsi = os.environ['DJANGO_SETTINGS_MODULE'].rfind('.')
        cms_settings = 'cms.envs{0}'.format(os.environ['DJANGO_SETTINGS_MODULE'][bsi:])

        cmd = 'DJANGO_SETTINGS_MODULE={3} PYTHONPATH=$PYTHONPATH:{2} {0} "{1}"'.format(
            acscript, gitloc, getattr(settings, 'REPO_ROOT'), cms_settings)

        logging.debug(_('Adding course with command: {0}').format(cmd))
        ret = subprocess.Popen(cmd, shell=True, executable='/bin/bash',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE).communicate()
        ret = ''.join(ret)
        msg = "<font color='red'>{0} {1}</font>".format(
                    _('Added course from'), gitloc)
        msg += "<pre>{0}</pre>".format(escape(ret))
        return msg

    cdir = (gitloc.rsplit('/', 1)[1])[:-4]
    gdir = settings.DATA_DIR / cdir
    if os.path.exists(gdir):
        msg += _("The course {0} already exists in the data directory! (reloading anyway)").format(cdir)
    else:
        cmd = 'cd {0}; git clone {1}'.format(settings.DATA_DIR, gitloc)
        msg += '<pre>%s</pre>' % escape(os.popen(cmd).read())
    if not os.path.exists(gdir):
        msg += _('Failed to clone repository to {0}').format(gdir)
        return msg
    def_ms.try_load_course(cdir)  # load into modulestore
    errlog = def_ms.errored_courses.get(cdir, '')
    if errlog:
        msg += '<hr width="50%%"><pre>{0}</pre>'.format(escape(errlog))
    else:
        course = def_ms.courses[cdir]
        msg += _('Loaded course %s (%s)<br/>Errors:').format(cdir,
                course.display_name)
        errors = def_ms.get_item_errors(course.location)
        if not errors:
            msg += 'None'
        else:
            msg += '<ul>'
            for (summary, err) in errors:
                msg += \
                    '<li><pre>{0}: {1}</pre></li>'.format(escape(summary),
                        escape(err))
            msg += '</ul>'
        datatable['data'].append([course.display_name, cdir]
                                 + git_info_for_course(cdir))
    return msg


def fix_external_auth_map_passwords():
    msg = ''
    for eamap in ExternalAuthMap.objects.all():
        u = eamap.user
        pw = eamap.internal_password
        if u is None:
            continue
        try:
            testuser = authenticate(username=u.username, password=pw)
        except Exception, err:
            msg += _('Failed in authenticating {0}, error {1}\n'
                     ).format(u, err)
            continue
        if testuser is None:
            msg += _('Failed in authenticating {0}').format(u)
            msg += _('fixed password')
            u.set_password(pw)
            u.save()
            continue
    if not msg:
        msg = _('All ok!')
    return msg

def create_user(uname, name, do_mit=False):

    if not uname:
        return _('Must provide username')
    if not name:
        return _('Must provide full name')

    make_eamap = False

    msg = ''
    if do_mit:
        if not '@' in uname:
            email = '{0}@MIT.EDU'.format(uname)
        else:
            email = uname
        if not email.endswith('@MIT.EDU'):
            msg += 'email must end in @MIT.EDU'
            return msg
        mit_domain = 'ssl:MIT'
        if ExternalAuthMap.objects.filter(external_id=email,
                external_domain=mit_domain):
            msg += _('Failed - email {0} already exists as external_id'
                     ).format(email)
            return msg
        make_eamap = True
    else:
        email = uname
        if not '@' in email:
            msg += _('email address required (not username)')
            return msg
    password = generate_password()
    user = User(username=uname, email=email, is_active=True)
    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        msg += _('Oops, failed to create user {0}, IntegrityError'
                 ).format(user)
        return msg

    r = Registration()
    r.register(user)

    up = UserProfile(user=user)
    up.name = name
    up.save()

    if make_eamap:
        credentials = \
            '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'.format(name, email)
        eamap = ExternalAuthMap(
            external_id=email,
            external_email=email,
            external_domain=mit_domain,
            external_name=name,
            internal_password=password,
            external_credentials=json.dumps(credentials),
            )
        eamap.user = user
        eamap.dtsignup = datetime.now()
        eamap.save()

    msg += _('User {0} created successfully!').format(user)
    return msg

def delete_user(uname):
    if not uname:
        return _('Must provide username')
    if '@' in uname:
        try:
            u = User.objects.get(email=uname)
        except Exception, err:
            msg = _('Cannot find user with email address {0}'
                    ).format(uname)
            return msg
    else:
        try:
            u = User.objects.get(username=uname)
        except Exception, err:
            msg = _('Cannot find user with username {0} - {1}').format(uname,
                                                                       err.msg)
            return msg
    u.delete()
    return _('Deleted user {0}').format(uname)

def return_csv(fn, datatable, fp=None):

    if fp is None:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename={0}'.format(fn)
    else:
        response = fp
    writer = csv.writer(response, dialect='excel', quotechar='"',
                        quoting=csv.QUOTE_ALL)
    writer.writerow(datatable['header'])
    for datarow in datatable['data']:
        encoded_row = [unicode(s).encode('utf-8') for s in datarow]
        writer.writerow(encoded_row)
    return response

def get_staff_group(course):

    return get_group(course, 'staff')

def get_instructor_group(course):

    return get_group(course, 'instructor')

def get_group(course, groupname):

    grpname = get_access_group_name(course, groupname)
    try:
        group = Group.objects.get(name=grpname)
    except Group.DoesNotExist:
        group = Group(name=grpname)  # create the group
        group.save()
    return group

@staff_member_required
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def sysadmin_dashboard(request):
    """
    Sysadmin dashboard.
    
    Provides:
        
        1. enrollment numbers
        2. loading new courses from github
        3. reloading XML from files

    """

    msg = ''
    plots = []
    datatable = {}

    def_ms = modulestore()
    is_using_mongo = 'mongo' in str(def_ms.__class__)

    if is_using_mongo:
        courses = def_ms.get_courses()
        courses = dict([c.id, c] for c in courses)  # no course directory
    else:
        courses = def_ms.courses.items()

    # the sysadmin dashboard page is modal: status, courses, enrollment,
    # staffing, gitlogs
    # keep that state in request.session (defaults to status mode)
    dash_mode = request.POST.get('dash_mode','')
    if dash_mode:
        request.session['dash_mode'] = dash_mode
    else:
        dash_mode = request.session.get('dash_mode', 'Status')

    # default datatable depends on dash_mode
    if dash_mode == 'Status':
        datatable = dict(header=[_('Statistic'), _('Value')],
                         title=_('Site statistics'))
        datatable['data'] = [[_('Total number of users'),
                             User.objects.all().count()]]
    elif dash_mode == 'Courses':
        data = []
        for (cdir, course) in courses.items():
            data.append([course.display_name, cdir]
                        + git_info_for_course(cdir))

        datatable = dict(header=[_('Course Name'), _('dir'),
                         _('git commit'), _('last change'),
                         _('last editor')],
                         title=_('Information about all courses'),
                         data=data)
    elif dash_mode == 'Enrollment' or dash_mode == 'Staffing':
        data = []

        for (cdir, course) in courses.items():
            datum = [course.display_name, course.id]
            datum += \
                [CourseEnrollment.objects.filter(course_id=course.id).count()]
            datum += [get_group(course, 'staff').user_set.all().count()]
            datum += [','.join([x.username for x in get_group(course,
                      'instructor').user_set.all()])]
            data.append(datum)

        datatable = dict(header=[_('Course Name'), _('course_id'),
                         _('# enrolled'), _('# staff'), _('instructors'
                         )],
                         title=_('Enrollment information for all courses'
                         ), data=data)

    # process actions from form POST
    action = request.POST.get('action', '')
    track.views.server_track(request, action, {}, page='sysdashboard')

    if _('Download list of all users (csv file)') in action:
        datatable = dict(header=[_('username'), _('email')],
                         title=_('List of all users'),
                         data=[[u.username, u.email] for u in
                         User.objects.all()])
        return return_csv('users_{0}.csv'.format(request.META['SERVER_NAME'
                          ]), datatable)

    elif _('Check and repair external Auth Map') in action:
        msg += '<pre>'
        msg += fix_external_auth_map_passwords()
        msg += '</pre>'
        datatable = {}

    elif _('Create user') in action:
        uname = request.POST.get('student_uname', '').strip()
        name = request.POST.get('student_fullname', '').strip()
        msg += create_user(uname, name, 
                           do_mit=settings.MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'])
    elif _('Delete user') in action:
        uname = request.POST.get('student_uname', '').strip()
        msg += delete_user(uname)

    elif _('Download staff and instructor list (csv file)') in action:
        data = []
        roles = ['instructor','staff']

        for cdir, course in courses.items():
            for role in roles:
                for u in get_group(course, role).user_set.all():
                    datum = [course.id, role, u.username, u.email,
                             u.profile.name]
                    data.append(datum)
        datatable = dict(header=[_('course_id'), _('role'), _('username'
                         ), _('email'), _('full_name')],
                         title=_('List of all course staff and instructors'
                         ), data=data)
        return return_csv('staff_{0}.csv'.format(request.META['SERVER_NAME'
                          ]), datatable)

    elif action == _('Delete course from site'):
        course_id = request.POST.get('course_id', '').strip()
        ok = False
        if course_id in courses:
            ok = True
            course = courses[course_id]
        else:
            try:
                course = get_course_by_id(course_id)
                ok = True
            except Exception, err:
                msg += \
                    _('Error - cannot get course with ID {0}<br/><pre>{1}</pre>'
                      ).format(course_id, escape(err))

        if ok and not is_using_mongo:
            cdir = course.metadata.get('data_dir',
                    course.location.course)
            def_ms.courses.pop(cdir)

            # now move the directory (don't actually delete it)
            nd = cdir + '_deleted_{0}'.format(int(time.time()))
            os.rename(settings.DATA_DIR / cdir, settings.DATA_DIR / nd)
            os.system('chmod -x {0}'.format((settings.DATA_DIR / nd)))

            msg += "<font color='red'>Deleted {0} = {1} ({3})</font>".format(cdir, course.id, course.display_name)

        elif ok and is_using_mongo:
            # delete course that is stored with mongodb backend
            loc = course.location
            cs = contentstore()
            commit = True
            delete_course(def_ms, cs, loc, commit)
            # don't delete user permission groups, though
            msg += \
                "<font color='red'>{0} {1} = {2} ({3})</font>".format(_('Deleted'
                    ), loc, course.id, course.display_name)

    elif action == _('Load new course from github'):
        gitloc = request.POST.get('repo_location', ''
                                  ).strip().replace(' ', '').replace(';'
                , '')
        msg += get_course_from_git(gitloc, is_using_mongo, def_ms, datatable)

    else:	# default to showing status summary
        msg += '<h2>{0}</h2>'.format(_('Courses loaded in the modulestore'))
        msg += '<ol>'
        for cdir, course in courses.items():
            msg += '<li>{0} ({1})</li>'.format(escape(cdir),
                    course.location.url())
        msg += '</ol>'

    # ----------------------------------------
    # context for rendering

    context = {
        'datatable': datatable,
        'plots': plots,
        'msg': msg,
        'djangopid': os.getpid(),
        'modeflag': {dash_mode: 'selectedmode'},
        'mitx_version': getattr(settings, 'MITX_VERSION_STRING', ''),
        }

    return render_to_response('sysadmin_dashboard.html', context)
    
#-----------------------------------------------------------------------------

def view_git_logs(request, course_id=None):

    import mongoengine  # don't import that until we need it, here

    # Set defaults even if it isn't defined in settings
    mongo_db = {
        'host': 'localhost',
        'user': '',
        'password': '',
        'db': 'xlog',
    }

    # Allow overrides
    if hasattr(settings, 'MONGODB_LOG'):
        mongo_db['host'] = settings.MONGODB_LOG.get('host', mongo_db['host'])
        mongo_db['user'] = settings.MONGODB_LOG.get('user', mongo_db['user'])
        mongo_db['password'] = settings.MONGODB_LOG.get('password',
                                                        mongo_db['password'])
        mongo_db['db'] = settings.MONGODB_LOG.get('db', mongo_db['db'])

    class CourseImportLog(mongoengine.Document):
        course_id = mongoengine.StringField(max_length=128)
        location = mongoengine.StringField(max_length=168)
        import_log = mongoengine.StringField(max_length=20 * 65535)
        git_log = mongoengine.StringField(max_length=65535)
        repo_dir = mongoengine.StringField(max_length=128)
        created = mongoengine.DateTimeField()
        meta = {'indexes': ['course_id', 'created'],
                'allow_inheritance': False}

    mongouri = 'mongodb://{0}/{1}'.format(mongo_db['host'], mongo_db['db'])
    try:
        mdb = mongoengine.connect(mongo_db['db'], host=mongouri, 
                                  username=mongo_db['user'], 
                                  password=mongo_db['password']
                              )
    except mongoengine.connection.ConnectionError, e:
        logging.critical(_('Unable to connect to mongodb to save log, please check ' \
                'MONGODB_LOG settings'))

    if course_id is None:
        cilset = CourseImportLog.objects.all().order_by('-created')
    else:
        log.debug('course_id={0}'.format(course_id))
        cilset = CourseImportLog.objects.filter(course_id=course_id).order_by('-created')
        log.debug('cilset length={0}'.format(len(cilset)))
    context = {'cilset': cilset, 'course_id': course_id}

    return render_to_response('sysadmin_dashboard_gitlogs.html',
                              context)
