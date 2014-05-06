"""
This module creates a sysadmin dashboard for managing and viewing
courses.
"""
import csv
import json
import logging
import os
import subprocess
import time
import StringIO

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.generic.base import TemplateView
from django.views.decorators.http import condition
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
import mongoengine

from courseware.courses import get_course_by_id
import dashboard.git_import as git_import
from dashboard.git_import import GitImportError
from student.roles import CourseStaffRole, CourseInstructorRole
from dashboard.models import CourseImportLog
from external_auth.models import ExternalAuthMap
from external_auth.views import generate_password
from student.models import CourseEnrollment, UserProfile, Registration
import track.views
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import XML_MODULESTORE_TYPE
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.store_utilities import delete_course
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.locations import SlashSeparatedCourseKey


log = logging.getLogger(__name__)


class SysadminDashboardView(TemplateView):
    """Base class for sysadmin dashboard views with common methods"""

    template_name = 'sysadmin_dashboard.html'

    def __init__(self, **kwargs):
        """
        Initialize base sysadmin dashboard class with modulestore,
        modulestore_type and return msg
        """

        self.def_ms = modulestore()
        self.is_using_mongo = True
        if isinstance(self.def_ms, XMLModuleStore):
            self.is_using_mongo = False
        self.msg = u''
        self.datatable = []
        super(SysadminDashboardView, self).__init__(**kwargs)

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True,
                                    must_revalidate=True))
    @method_decorator(condition(etag_func=None))
    def dispatch(self, *args, **kwargs):
        return super(SysadminDashboardView, self).dispatch(*args, **kwargs)

    def get_courses(self):
        """ Get an iterable list of courses."""

        courses = self.def_ms.get_courses()
        courses = dict([c.id, c] for c in courses)  # no course directory

        return courses

    def return_csv(self, filename, header, data):
        """
        Convenient function for handling the http response of a csv.
        data should be iterable and is used to stream object over http
        """

        csv_file = StringIO.StringIO()
        writer = csv.writer(csv_file, dialect='excel', quotechar='"',
                            quoting=csv.QUOTE_ALL)

        writer.writerow(header)

        # Setup streaming of the data
        def read_and_flush():
            """Read and clear buffer for optimization"""
            csv_file.seek(0)
            csv_data = csv_file.read()
            csv_file.seek(0)
            csv_file.truncate()
            return csv_data

        def csv_data():
            """Generator for handling potentially large CSVs"""
            for row in data:
                writer.writerow(row)
            csv_data = read_and_flush()
            yield csv_data
        response = HttpResponse(csv_data(), mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
        return response


class Users(SysadminDashboardView):
    """
    The status view provides Web based user management, a listing of
    courses loaded, and user statistics
    """

    def fix_external_auth_map_passwords(self):
        """
        This corrects any passwords that have drifted from eamap to
        internal django auth.  Needs to be removed when fixed in external_auth
        """

        msg = ''
        for eamap in ExternalAuthMap.objects.all():
            euser = eamap.user
            epass = eamap.internal_password
            if euser is None:
                continue
            try:
                testuser = authenticate(username=euser.username, password=epass)
            except (TypeError, PermissionDenied, AttributeError), err:
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

    def create_user(self, uname, name, password=None):
        """ Creates a user (both SSL and regular)"""

        if not uname:
            return _('Must provide username')
        if not name:
            return _('Must provide full name')

        email_domain = getattr(settings, 'SSL_AUTH_EMAIL_DOMAIN', 'MIT.EDU')

        msg = u''
        if settings.FEATURES['AUTH_USE_CERTIFICATES']:
            if not '@' in uname:
                email = '{0}@{1}'.format(uname, email_domain)
            else:
                email = uname
            if not email.endswith('@{0}'.format(email_domain)):
                msg += u'{0} @{1}'.format(_('email must end in'), email_domain)
                return msg
            mit_domain = 'ssl:MIT'
            if ExternalAuthMap.objects.filter(external_id=email,
                                              external_domain=mit_domain):
                msg += _('Failed - email {0} already exists as '
                         'external_id').format(email)
                return msg
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
            msg += _('Oops, failed to create user {0}, '
                     'IntegrityError').format(user)
            return msg

        reg = Registration()
        reg.register(user)

        profile = UserProfile(user=user)
        profile.name = name
        profile.save()

        if settings.FEATURES['AUTH_USE_CERTIFICATES']:
            credential_string = getattr(settings, 'SSL_AUTH_DN_FORMAT_STRING',
                                        '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}')
            credentials = credential_string.format(name, email)
            eamap = ExternalAuthMap(
                external_id=email,
                external_email=email,
                external_domain=mit_domain,
                external_name=name,
                internal_password=new_password,
                external_credentials=json.dumps(credentials),
            )
            eamap.user = user
            eamap.dtsignup = timezone.now()
            eamap.save()

        msg += _('User {0} created successfully!').format(user)
        return msg

    def delete_user(self, uname):
        """Deletes a user from django auth"""

        if not uname:
            return _('Must provide username')
        if '@' in uname:
            try:
                user = User.objects.get(email=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with email address {0}').format(uname)
                return msg
        else:
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with username {0} - {1}'
                        ).format(uname, str(err))
                return msg
        user.delete()
        return _('Deleted user {0}').format(uname)

    def make_common_context(self):
        """Returns the datatable used for this view"""

        self.datatable = {}
        courses = self.get_courses()

        self.datatable = dict(header=[_('Statistic'), _('Value')],
                              title=_('Site statistics'))
        self.datatable['data'] = [[_('Total number of users'),
                                   User.objects.all().count()]]

        self.msg += u'<h2>{0}</h2>'.format(
            _('Courses loaded in the modulestore'))
        self.msg += u'<ol>'
        for (cdir, course) in courses.items():
            self.msg += u'<li>{0} ({1})</li>'.format(
                escape(cdir), course.location.to_deprecated_string())
        self.msg += u'</ol>'

    def get(self, request):

        if not request.user.is_staff:
            raise Http404
        self.make_common_context()

        context = {
            'datatable': self.datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle various actions available on page"""

        if not request.user.is_staff:
            raise Http404

        self.make_common_context()

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {}, page='user_sysdashboard')

        if action == 'download_users':
            header = [_('username'), _('email'), ]
            data = ([u.username, u.email] for u in
                    (User.objects.all().iterator()))
            return self.return_csv('users_{0}.csv'.format(
                request.META['SERVER_NAME']), header, data)
        elif action == 'repair_eamap':
            self.msg = u'<h4>{0}</h4><pre>{1}</pre>{2}'.format(
                _('Repair Results'),
                self.fix_external_auth_map_passwords(),
                self.msg)
            self.datatable = {}
        elif action == 'create_user':
            uname = request.POST.get('student_uname', '').strip()
            name = request.POST.get('student_fullname', '').strip()
            password = request.POST.get('student_password', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />{2}'.format(
                _('Create User Results'),
                self.create_user(uname, name, password), self.msg)
        elif action == 'del_user':
            uname = request.POST.get('student_uname', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />{2}'.format(
                _('Delete User Results'), self.delete_user(uname), self.msg)

        context = {
            'datatable': self.datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)


class Courses(SysadminDashboardView):
    """
    This manages adding/updating courses from git, deleting courses, and
    provides course listing information.
    """

    def git_info_for_course(self, cdir):
        """This pulls out some git info like the last commit"""

        cmd = ''
        gdir = settings.DATA_DIR / cdir
        info = ['', '', '']
        if not os.path.exists(gdir):
            return info

        cmd = ['git', 'log', '-1',
               '--format=format:{ "commit": "%H", "author": "%an %ae", "date": "%ad"}', ]
        try:
            output_json = json.loads(subprocess.check_output(cmd, cwd=gdir))
            info = [output_json['commit'],
                    output_json['date'],
                    output_json['author'], ]
        except (ValueError, subprocess.CalledProcessError):
            pass

        return info

    def get_course_from_git(self, gitloc, branch, datatable):
        """This downloads and runs the checks for importing a course in git"""

        if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
                gitloc.startswith('https:') or gitloc.startswith('git:')):
            return _("The git repo location should end with '.git', "
                     "and be a valid url")

        if self.is_using_mongo:
            return self.import_mongo_course(gitloc, branch)

        return self.import_xml_course(gitloc, branch, datatable)

    def import_mongo_course(self, gitloc, branch):
        """
        Imports course using management command and captures logging output
        at debug level for display in template
        """

        msg = u''

        log.debug('Adding course using git repo {0}'.format(gitloc))

        # Grab logging output for debugging imports
        output = StringIO.StringIO()
        import_log_handler = logging.StreamHandler(output)
        import_log_handler.setLevel(logging.DEBUG)

        logger_names = ['xmodule.modulestore.xml_importer',
                        'dashboard.git_import',
                        'xmodule.modulestore.xml',
                        'xmodule.seq_module', ]
        loggers = []

        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(import_log_handler)
            loggers.append(logger)

        error_msg = ''
        try:
            git_import.add_repo(gitloc, None, branch)
        except GitImportError as ex:
            error_msg = str(ex)
        ret = output.getvalue()

        # Remove handler hijacks
        for logger in loggers:
            logger.setLevel(logging.NOTSET)
            logger.removeHandler(import_log_handler)

        if error_msg:
            msg_header = error_msg
            color = 'red'
        else:
            msg_header = _('Added Course')
            color = 'blue'

        msg = u"<h4 style='color:{0}'>{1}</h4>".format(color, msg_header)
        msg += "<pre>{0}</pre>".format(escape(ret))
        return msg

    def import_xml_course(self, gitloc, branch, datatable):
        """Imports a git course into the XMLModuleStore"""

        msg = u''
        if not getattr(settings, 'GIT_IMPORT_WITH_XMLMODULESTORE', False):
            return _('Refusing to import. GIT_IMPORT_WITH_XMLMODULESTORE is '
                     'not turned on, and it is generally not safe to import '
                     'into an XMLModuleStore with multithreaded. We '
                     'recommend you enable the MongoDB based module store '
                     'instead, unless this is a development environment.')
        cdir = (gitloc.rsplit('/', 1)[1])[:-4]
        gdir = settings.DATA_DIR / cdir
        if os.path.exists(gdir):
            msg += _("The course {0} already exists in the data directory! "
                     "(reloading anyway)").format(cdir)
            cmd = ['git', 'pull', ]
            cwd = gdir
        else:
            cmd = ['git', 'clone', gitloc, ]
            cwd = settings.DATA_DIR
        cwd = os.path.abspath(cwd)
        try:
            cmd_output = escape(
                subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=cwd)
            )
        except subprocess.CalledProcessError as ex:
            log.exception('Git pull or clone output was: %r', ex.output)
            # Translators: unable to download the course content from
            # the source git repository. Clone occurs if this is brand
            # new, and pull is when it is being updated from the
            # source.
            return _('Unable to clone or pull repository. Please check '
                     'your url. Output was: {0!r}'.format(ex.output))

        msg += u'<pre>{0}</pre>'.format(cmd_output)
        if not os.path.exists(gdir):
            msg += _('Failed to clone repository to {0}').format(gdir)
            return msg
        # Change branch if specified
        if branch:
            try:
                git_import.switch_branch(branch, gdir)
            except GitImportError as ex:
                return str(ex)
            # Translators: This is a git repository branch, which is a
            # specific version of a courses content
            msg += u'<p>{0}</p>'.format(
                _('Successfully switched to branch: '
                  '{branch_name}'.format(branch_name=branch)))

        self.def_ms.try_load_course(os.path.abspath(gdir))
        errlog = self.def_ms.errored_courses.get(cdir, '')
        if errlog:
            msg += u'<hr width="50%"><pre>{0}</pre>'.format(escape(errlog))
        else:
            course = self.def_ms.courses[os.path.abspath(gdir)]
            msg += _('Loaded course {0} {1}<br/>Errors:').format(
                cdir, course.display_name)
            errors = self.def_ms.get_course_errors(course.id)
            if not errors:
                msg += u'None'
            else:
                msg += u'<ul>'
                for (summary, err) in errors:
                    msg += u'<li><pre>{0}: {1}</pre></li>'.format(escape(summary),
                                                                  escape(err))
                msg += u'</ul>'
            datatable['data'].append([course.display_name, cdir]
                                     + self.git_info_for_course(cdir))
        return msg

    def make_datatable(self):
        """Creates course information datatable"""

        data = []
        courses = self.get_courses()

        for (cdir, course) in courses.items():
            gdir = cdir.run
            data.append([course.display_name, cdir]
                        + self.git_info_for_course(gdir))

        return dict(header=[_('Course Name'), _('Directory/ID'),
                            _('Git Commit'), _('Last Change'),
                            _('Last Editor')],
                    title=_('Information about all courses'),
                    data=data)

    def get(self, request):
        """Displays forms and course information"""

        if not request.user.is_staff:
            raise Http404

        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'courses': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle all actions from courses view"""

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {},
                                 page='courses_sysdashboard')

        courses = self.get_courses()
        if action == 'add_course':
            gitloc = request.POST.get('repo_location', '').strip().replace(' ', '').replace(';', '')
            branch = request.POST.get('repo_branch', '').strip().replace(' ', '').replace(';', '')
            datatable = self.make_datatable()
            self.msg += self.get_course_from_git(gitloc, branch, datatable)

        elif action == 'del_course':
            course_id = request.POST.get('course_id', '').strip()
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            course_found = False
            if course_key in courses:
                course_found = True
                course = courses[course_key]
            else:
                try:
                    course = get_course_by_id(course_key)
                    course_found = True
                except Exception, err:   # pylint: disable=broad-except
                    self.msg += _('Error - cannot get course with ID '
                                  '{0}<br/><pre>{1}</pre>').format(
                                      course_id, escape(str(err))
                                  )

            is_xml_course = (modulestore().get_modulestore_type(course_key) == XML_MODULESTORE_TYPE)
            if course_found and is_xml_course:
                cdir = course.data_dir
                self.def_ms.courses.pop(cdir)

                # now move the directory (don't actually delete it)
                new_dir = "{course_dir}_deleted_{timestamp}".format(
                    course_dir=cdir,
                    timestamp=int(time.time())
                )
                os.rename(settings.DATA_DIR / cdir, settings.DATA_DIR / new_dir)

                self.msg += (u"<font color='red'>Deleted "
                             u"{0} = {1} ({2})</font>".format(
                                 cdir, course.id, course.display_name))

            elif course_found and not is_xml_course:
                # delete course that is stored with mongodb backend
                content_store = contentstore()
                commit = True
                delete_course(self.def_ms, content_store, course.id, commit)
                # don't delete user permission groups, though
                self.msg += \
                    u"<font color='red'>{0} {1} ({2})</font>".format(
                        _('Deleted'), course.id.to_deprecated_string(), course.display_name)
            datatable = self.make_datatable()

        context = {
            'datatable': datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'courses': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)


class Staffing(SysadminDashboardView):
    """
    The status view provides a view of staffing and enrollment in
    courses that include an option to download the data as a csv.
    """

    def get(self, request):
        """Displays course Enrollment and staffing course statistics"""

        if not request.user.is_staff:
            raise Http404
        data = []

        courses = self.get_courses()

        for (cdir, course) in courses.items():  # pylint: disable=unused-variable
            datum = [course.display_name, course.id]
            datum += [CourseEnrollment.objects.filter(
                course_id=course.id).count()]
            datum += [CourseStaffRole(course.id).users_with_role().count()]
            datum += [','.join([x.username for x in CourseInstructorRole(
                course.id).users_with_role()])]
            data.append(datum)

        datatable = dict(header=[_('Course Name'), _('course_id'),
                                 _('# enrolled'), _('# staff'),
                                 _('instructors')],
                         title=_('Enrollment information for all courses'),
                         data=data)
        context = {
            'datatable': datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'staffing': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle all actions from staffing and enrollment view"""

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {},
                                 page='staffing_sysdashboard')

        if action == 'get_staff_csv':
            data = []
            roles = [CourseInstructorRole, CourseStaffRole, ]

            courses = self.get_courses()

            for (cdir, course) in courses.items():  # pylint: disable=unused-variable
                for role in roles:
                    for user in role(course.id).users_with_role():
                        datum = [course.id, role, user.username, user.email,
                                 user.profile.name]
                        data.append(datum)
            header = [_('course_id'),
                      _('role'), _('username'),
                      _('email'), _('full_name'), ]
            return self.return_csv('staff_{0}.csv'.format(
                request.META['SERVER_NAME']), header, data)

        return self.get(request)


class GitLogs(TemplateView):
    """
    This provides a view into the import of courses from git repositories.
    It is convenient for allowing course teams to see what may be wrong with
    their xml
    """

    template_name = 'sysadmin_dashboard_gitlogs.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Shows logs of imports that happened as a result of a git import"""

        course_id = kwargs.get('course_id')
        if course_id:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        # Set mongodb defaults even if it isn't defined in settings
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

        mongouri = 'mongodb://{user}:{password}@{host}/{db}'.format(**mongo_db)

        error_msg = ''

        try:
            if mongo_db['user'] and mongo_db['password']:
                mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
            else:
                mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'])
        except mongoengine.connection.ConnectionError:
            log.exception('Unable to connect to mongodb to save log, '
                          'please check MONGODB_LOG settings.')

        if course_id is None:
            # Require staff if not going to specific course
            if not request.user.is_staff:
                raise Http404
            cilset = CourseImportLog.objects.all().order_by('-created')
        else:
            try:
                course = get_course_by_id(course_id)
            except Exception:  # pylint: disable=broad-except
                log.info('Cannot find course {0}'.format(course_id))
                raise Http404

            # Allow only course team, instructors, and staff
            if not (request.user.is_staff or
                    CourseInstructorRole(course.id).has_user(request.user) or
                    CourseStaffRole(course.id).has_user(request.user)):
                raise Http404
            log.debug('course_id={0}'.format(course_id))
            cilset = CourseImportLog.objects.filter(course_id=course_id).order_by('-created')
            log.debug('cilset length={0}'.format(len(cilset)))
        mdb.disconnect()
        context = {'cilset': cilset,
                   'course_id': course_id.to_deprecated_string() if course_id else None,
                   'error_msg': error_msg}

        return render_to_response(self.template_name, context)
