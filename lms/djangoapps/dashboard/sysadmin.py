"""
This module creates a sysadmin dashboard for managing and viewing
courses.
"""
import csv
import json
import logging
import os
import time
import imp
import StringIO

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
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils.html import escape
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404

from mitxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.store_utilities import delete_course
import mongoengine

import track.views

log = logging.getLogger(__name__)


class CourseImportLog(mongoengine.Document):
    """Mongoengine model for git log"""
    # pylint: disable-msg=R0924

    course_id = mongoengine.StringField(max_length=128)
    location = mongoengine.StringField(max_length=168)
    import_log = mongoengine.StringField(max_length=20 * 65535)
    git_log = mongoengine.StringField(max_length=65535)
    repo_dir = mongoengine.StringField(max_length=128)
    created = mongoengine.DateTimeField()
    meta = {'indexes': ['course_id', 'created'],
            'allow_inheritance': False}


def git_info_for_course(cdir):
    """This pulls out some git info like the last commit"""

    cmd = ''
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
    """This downloads and runs the checks for importing a course in git"""

    msg = u''
    if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
       gitloc.startswith('https:') or gitloc.startswith('git:')):
        msg += \
            _("The git repo location should end with '.git', and be a valid url")
        return msg

    if is_using_mongo:
        acscript = getattr(settings, 'GIT_ADD_COURSE_SCRIPT', '')
        if not acscript or not os.path.exists(acscript):
            msg = u"<font color='red'>{0} - {1}</font>".format(
                _('Must configure GIT_ADD_COURSE_SCRIPT in settings first!'), acscript)
            return msg

        # import course script directly and call add_repo function
        git_add_script = imp.load_source('git_add_script', acscript)
        logging.debug(
            _('Adding course using add repo from {0} and repo {1}').format(
                acscript, gitloc))

        # Grab logging output for debugging imports
        output = StringIO.StringIO()

        import_logger = logging.getLogger(
            'xmodule.modulestore.xml_importer')
        git_logger = logging.getLogger('git_add_script')
        xml_logger = logging.getLogger('xmodule.modulestore.xml')

        import_log_handler = logging.StreamHandler(output)
        import_log_handler.setLevel(logging.DEBUG)

        for logger in [import_logger, git_logger, xml_logger, ]:
            logger.old_level = logger.level
            logger.setLevel(logging.DEBUG)
            logger.addHandler(import_log_handler)

        git_add_script.add_repo(gitloc, None)

        ret = output.getvalue()

        # Remove handler hijacks
        for logger in [import_logger, git_logger, xml_logger, ]:
            logger.setLevel(logger.old_level)
            logger.removeHandler(import_log_handler)
        msg = u"<font color='red'>{0} {1}</font>".format(
            _('Added course from'), gitloc)
        msg += _("<pre>{0}</pre>").format(escape(ret))
        return msg

    cdir = (gitloc.rsplit('/', 1)[1])[:-4]
    gdir = settings.DATA_DIR / cdir
    if os.path.exists(gdir):
        msg += _("The course {0} already exists in the data directory! "
                 "(reloading anyway)").format(cdir)
        cmd = 'cd {0}; git pull'.format(settings.DATA_DIR, gitloc)
    else:
        cmd = 'cd {0}; git clone {1}'.format(settings.DATA_DIR, gitloc)
        msg += u'<pre>%s</pre>' % escape(os.popen(cmd).read())
    if not os.path.exists(gdir):
        msg += _('Failed to clone repository to {0}').format(gdir)
        return msg
    def_ms.try_load_course(os.path.abspath(gdir))  # load into modulestore
    errlog = def_ms.errored_courses.get(cdir, '')
    if errlog:
        msg += u'<hr width="50%"><pre>{0}</pre>'.format(escape(errlog))
    else:
        course = def_ms.courses[os.path.abspath(gdir)]
        msg += _('Loaded course {0} {1}<br/>Errors:').format(cdir,
                                                             course.display_name)
        errors = def_ms.get_item_errors(course.location)
        if not errors:
            msg += u'None'
        else:
            msg += u'<ul>'
            for (summary, err) in errors:
                msg += \
                    u'<li><pre>{0}: {1}</pre></li>'.format(escape(summary),
                                                           escape(err))
            msg += u'</ul>'
        datatable['data'].append([course.display_name, cdir]
                                 + git_info_for_course(cdir))
    return msg


def fix_external_auth_map_passwords():
    """
    This corrects any passwords that have drifted from eamp to
    internal django auth
    """

    msg = ''
    for eamap in ExternalAuthMap.objects.all():
        euser = eamap.user
        epass = eamap.internal_password
        if euser is None:
            continue
        try:
            testuser = authenticate(username=euser.username, password=epass)
        except (TypeError, PermissionDenied), err:
            msg += _('Failed in authenticating {0}, error {1}\n'
                     ).format(euser, err)
            continue
        if testuser is None:
            msg += _('Failed in authenticating {0}\n').format(euser)
            msg += _('fixed password')
            euser.set_password(epass)
            euser.save()
            continue
    if not msg:
        msg = _('All ok!')
    return msg


def create_user(uname, name, password=None, do_mit=False):
    """ Creates a user (both SSL and regular)"""

    if not uname:
        return _('Must provide username')
    if not name:
        return _('Must provide full name')

    make_eamap = False

    msg = u''
    if do_mit:
        if not '@' in uname:
            email = '{0}@MIT.EDU'.format(uname)
        else:
            email = uname
        if not email.endswith('@MIT.EDU'):
            msg += u'email must end in @MIT.EDU'
            return msg
        mit_domain = 'ssl:MIT'
        if ExternalAuthMap.objects.filter(external_id=email,
                                          external_domain=mit_domain):
            msg += _('Failed - email {0} already exists as external_id'
                     ).format(email)
            return msg
        make_eamap = True
        new_password = generate_password()
    else:
        if not password:
            return _('Password must be supplied if not using certificates')

        email = uname

        if not '@' in email:
            msg += _('email address required (not username)')
            return msg
        new_password = password

    user = User(username=uname, email=email, is_active=True)
    user.set_password(new_password)
    try:
        user.save()
    except IntegrityError:
        msg += _('Oops, failed to create user {0}, IntegrityError'
                 ).format(user)
        return msg

    reg = Registration()
    reg.register(user)

    profile = UserProfile(user=user)
    profile.name = name
    profile.save()

    if make_eamap:
        credentials = \
            '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'.format(name, email)
        eamap = ExternalAuthMap(
            external_id=email,
            external_email=email,
            external_domain=mit_domain,
            external_name=name,
            internal_password=new_password,
            external_credentials=json.dumps(credentials),
        )
        eamap.user = user
        eamap.dtsignup = datetime.now()
        eamap.save()

    msg += _('User {0} created successfully!').format(user)
    return msg


def delete_user(uname):
    """Deletes a user from django auth"""

    if not uname:
        return _('Must provide username')
    if '@' in uname:
        try:
            user = User.objects.get(email=uname)
        except User.DoesNotExist, err:
            msg = _('Cannot find user with email address {0}'
                    ).format(uname)
            return msg
    else:
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist, err:
            msg = _('Cannot find user with username {0} - {1}'
                    ).format(uname, err.msg)
            return msg
    user.delete()
    return _('Deleted user {0}').format(uname)


def return_csv(filename, datatable):
    """Convenient function for handling the http response of a csv"""

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)

    writer = csv.writer(response, dialect='excel', quotechar='"',
                        quoting=csv.QUOTE_ALL)
    writer.writerow(datatable['header'])
    for datarow in datatable['data']:
        encoded_row = [unicode(s).encode('utf-8') for s in datarow]
        writer.writerow(encoded_row)
    return response


def get_staff_group(course):
    """Gets staff members for course"""

    return get_group(course, 'staff')


def get_instructor_group(course):
    """Gets instructors for course"""

    return get_group(course, 'instructor')


def get_group(course, groupname):
    """Gets the course group"""

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
    # pylint: disable-msg=R0915

    msg = u''
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
    dash_mode = request.POST.get('dash_mode', '')
    if dash_mode:
        request.session['dash_mode'] = dash_mode
    else:
        dash_mode = request.session.get('dash_mode', _('Status'))

    # default datatable depends on dash_mode
    if dash_mode == _('Status'):
        datatable = dict(header=[_('Statistic'), _('Value')],
                         title=_('Site statistics'))
        datatable['data'] = [[_('Total number of users'),
                             User.objects.all().count()]]
    elif dash_mode == _('Courses'):
        data = []

        if hasattr(courses, 'items'):
            course_iter = courses.items()
        else:
            course_iter = courses
        for (cdir, course) in course_iter:
            data.append([course.display_name, cdir]
                        + git_info_for_course(cdir))

        datatable = dict(header=[_('Course Name'), _('dir'),
                         _('git commit'), _('last change'),
                         _('last editor')],
                         title=_('Information about all courses'),
                         data=data)
    elif dash_mode == _('Staffing and Enrollment'):
        data = []

        if hasattr(courses, 'items'):
            course_iter = courses.items()
        else:
            course_iter = courses
        for (cdir, course) in course_iter:
            datum = [course.display_name, course.id]
            datum += \
                [CourseEnrollment.objects.filter(course_id=course.id).count()]
            datum += [get_group(course, 'staff').user_set.all().count()]
            datum += [','.join([x.username for x in get_group(course,
                      'instructor').user_set.all()])]
            data.append(datum)

        datatable = dict(header=[_('Course Name'), _('course_id'),
                                 _('# enrolled'), _('# staff'), _('instructors')],
                         title=_('Enrollment information for all courses'),
                         data=data)

    # process actions from form POST
    action = request.POST.get('action', '')
    track.views.server_track(request, action, {}, page='sysdashboard')

    if _('Download list of all users (csv file)') in action:
        datatable = dict(header=[_('username'), _('email')],
                         title=_('List of all users'),
                         data=[[u.username, u.email] for u in
                               User.objects.all()])
        return return_csv('users_{0}.csv'.format(
            request.META['SERVER_NAME']), datatable)
    elif _('Check and repair external Auth Map') in action:
        msg += u'<pre>'
        msg += fix_external_auth_map_passwords()
        msg += u'</pre>'
        datatable = {}
    elif _('Create user') in action:
        uname = request.POST.get('student_uname', '').strip()
        name = request.POST.get('student_fullname', '').strip()
        password = request.POST.get('student_password', '').strip()

        msg += create_user(uname, name, password,
                           do_mit=settings.MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'])
    elif _('Delete user') in action:
        uname = request.POST.get('student_uname', '').strip()
        msg += delete_user(uname)
    elif _('Download staff and instructor list (csv file)') in action:
        data = []
        roles = ['instructor', 'staff']

        if hasattr(courses, 'items'):
            course_iter = courses.items()
        else:
            course_iter = courses
        for (cdir, course) in course_iter:
            for role in roles:
                for user in get_group(course, role).user_set.all():
                    datum = [course.id, role, user.username, user.email,
                             user.profile.name]
                    data.append(datum)
        datatable = dict(header=[_('course_id'),
                                 _('role'), _('username'),
                                 _('email'), _('full_name')],
                         title=_('List of all course staff and instructors'),
                         data=data)
        return return_csv('staff_{0}.csv'.format(
            request.META['SERVER_NAME']), datatable)
    elif action == _('Delete course from site'):
        course_id = request.POST.get('course_id', '').strip()
        course_found = False
        if course_id in courses:
            course_found = True
            course = courses[course_id]
        else:
            try:
                course = get_course_by_id(course_id)
                course_found = True
            except Http404, err:
                msg += \
                    _('Error - cannot get course with ID {0}<br/><pre>{1}</pre>'
                      ).format(course_id, escape(err))

        if course_found and not is_using_mongo:
            cdir = course.data_dir
            def_ms.courses.pop(cdir)

            # now move the directory (don't actually delete it)
            new_dir = cdir + '_deleted_{0}'.format(int(time.time()))
            os.rename(settings.DATA_DIR / cdir, settings.DATA_DIR / new_dir)

            msg += u"<font color='red'>Deleted {0} = {1} ({2})</font>".format(
                cdir, course.id, course.display_name)

        elif course_found and is_using_mongo:
            # delete course that is stored with mongodb backend
            loc = course.location
            content_store = contentstore()
            commit = True
            delete_course(def_ms, content_store, loc, commit)
            # don't delete user permission groups, though
            msg += \
                u"<font color='red'>{0} {1} = {2} ({3})</font>".format(
                    _('Deleted'), loc, course.id, course.display_name)

    elif action == _('Load new course from github'):
        gitloc = request.POST.get('repo_location', '').strip().replace(
            ' ', '').replace(';', '')
        msg += get_course_from_git(gitloc, is_using_mongo, def_ms, datatable)

    # default to showing status summary
    else:
        if hasattr(courses, 'items'):
            course_iter = courses.items()
        else:
            course_iter = courses
        msg += u'<h2>{0}</h2>'.format(
            _('Courses loaded in the modulestore'))
        msg += u'<ol>'
        for (cdir, course) in course_iter:
            msg += u'<li>{0} ({1})</li>'.format(
                escape(cdir), course.location.url())
        msg += u'</ol>'

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


# -----------------------------------------------------------------------------

@staff_member_required
def view_git_logs(request, course_id=None):
    """Shows logs of imports that happened as a result of a git import"""
    # pylint: disable-msg=W0613

    # Set defaults even if it isn't defined in settings
    mongo_db = {
        'host': 'localhost',
        'user': '',
        'password': '',
        'db': 'xlog',
    }

    # Allow overrides
    if hasattr(settings, 'MONGODB_LOG'):
        for config_item in ['host', 'user', 'password', 'db', ]:
            mongo_db[config_item] = settings.MONGODB_LOG.get(
                config_item, mongo_db[config_item])

    mongouri = 'mongodb://{0}:{1}@{2}/{3}'.format(
        mongo_db['user'], mongo_db['password'],
        mongo_db['host'], mongo_db['db'])

    try:
        if mongo_db['user'] and mongo_db['password']:
            mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
        else:
            mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'])
    except mongoengine.connection.ConnectionError, ex:
        logging.critical(_('Unable to connect to mongodb to save log, please check '
                           'MONGODB_LOG settings. error: {0}').format(str(ex)))

    if course_id is None:
        cilset = CourseImportLog.objects.all().order_by('-created')
    else:
        log.debug('course_id={0}'.format(course_id))
        cilset = CourseImportLog.objects.filter(
            course_id=course_id).order_by('-created')
        log.debug('cilset length={0}'.format(len(cilset)))
    mdb.disconnect()
    context = {'cilset': cilset, 'course_id': course_id}

    return render_to_response('sysadmin_dashboard_gitlogs.html',
                              context)
