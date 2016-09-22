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

from pymongo.errors import PyMongoError

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.management import call_command
from django.db import transaction
from django.db import IntegrityError
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.generic.base import TemplateView
from django.views.decorators.http import condition
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
import mongoengine
from path import Path as path
import sys

from courseware.courses import get_course_by_id
import dashboard.git_import as git_import
from django_comment_client.management_utils import rename_user as rename_user_util
from dashboard.git_import import GitImportError
from dashboard.models import CourseImportLog
from external_auth.models import ExternalAuthMap
from external_auth.views import generate_password
from instructor_task.models import InstructorTask
from student.models import CourseEnrollment, UserProfile, Registration
from student.roles import CourseStaffRole, CourseInstructorRole
import track.views
from util.json_request import JsonResponse
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey


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
        if self.def_ms.get_modulestore_type(None) == 'xml':
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

        return self.def_ms.get_courses()

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
        response = HttpResponse(csv_data(), content_type='text/csv')
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
                # Translators: This message means that the user could not be authenticated (that is, we could
                # not log them in for some reason - maybe they don't have permission, or their password was wrong)
                msg += _('Failed in authenticating {username}, error {error}\n').format(
                    username=euser,
                    error=err
                )
                continue
            if testuser is None:
                # Translators: This message means that the user could not be authenticated (that is, we could
                # not log them in for some reason - maybe they don't have permission, or their password was wrong)
                msg += _('Failed in authenticating {username}\n').format(username=euser)
                # Translators: this means that the password has been corrected (sometimes the database needs to be resynchronized)
                # Translate this as meaning "the password was fixed" or "the password was corrected".
                msg += _('fixed password')
                euser.set_password(epass)
                euser.save()
                continue
        if not msg:
            # Translators: this means everything happened successfully, yay!
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
            if '@' not in uname:
                email = '{0}@{1}'.format(uname, email_domain)
            else:
                email = uname
            if not email.endswith('@{0}'.format(email_domain)):
                # Translators: Domain is an email domain, such as "@gmail.com"
                msg += _('Email address must end in {domain}').format(domain="@{0}".format(email_domain))
                return msg
            mit_domain = 'ssl:MIT'
            if ExternalAuthMap.objects.filter(external_id=email,
                                              external_domain=mit_domain):
                msg += _('Failed - email {email_addr} already exists as {external_id}').format(
                    email_addr=email,
                    external_id="external_id"
                )
                return msg
            new_password = generate_password()
        else:
            if not password:
                return _('Password must be supplied if not using certificates')

            email = uname

            if '@' not in email:
                msg += _('email address required (not username)')
                return msg
            new_password = password

        user = User(username=uname, email=email, is_active=True)
        user.set_password(new_password)
        try:
            user.save()
        except IntegrityError:
            msg += _('Oops, failed to create user {user}, {error}').format(
                user=user,
                error="IntegrityError"
            )
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

        msg += _('User {user} created successfully!').format(user=user)
        return msg

    def delete_user(self, uname):
        """Deletes a user from django auth"""

        if not uname:
            return _('Must provide username')
        if '@' in uname:
            try:
                user = User.objects.get(email=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with email address {email_addr}').format(email_addr=uname)
                return msg
        else:
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with username {username} - {error}').format(
                    username=uname,
                    error=str(err)
                )
                return msg
        user.delete()
        return _('Deleted user {username}').format(username=uname)

    def rename_user(self, username_old, username_new):
        """
        helper method that processes a username rename request
        :param username_old: the old username
        :param username_new: the new username
        :return: status message to display after the rename command is attempted
        """
        if not (username_old and username_new):
            message = _('Usernames cannot be blank')
        else:
            try:
                rename_user_util(username_old, username_new)
            except User.DoesNotExist:
                message = _("User '{username_old}' does not exist").format(
                    username_old=username_old,
                )
            except IntegrityError:
                message = _("User '{username_new}' already exists").format(
                    username_new=username_new,
                )
            except PyMongoError:
                message = _("Failed to modify username for user '{username_old}'").format(
                    username_old=username_old,
                )
            else:
                message = _("Changed username of user '{username_old}' to '{username_new}'").format(
                    username_old=username_old,
                    username_new=username_new,
                )
        return message

    def make_common_context(self):
        """Returns the datatable used for this view"""

        self.datatable = {}

        self.datatable = dict(header=[_('Statistic'), _('Value')],
                              title=_('Site statistics'))
        self.datatable['data'] = [[_('Total number of users'),
                                   User.objects.all().count()]]

        self.msg += u'<h2>{0}</h2>'.format(
            _('Courses loaded in the modulestore')
        )
        self.msg += u'<ol>'
        for course in self.get_courses():
            self.msg += u'<li>{0} ({1})</li>'.format(
                escape(course.id.to_deprecated_string()), course.location.to_deprecated_string())
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
        elif action == 'rename_user':
            username_old = request.POST.get('username_old', '').strip()
            username_new = request.POST.get('username_new', '').strip()
            self.msg = u"<h4>{title}</h4><p>{message}</p><hr />{message_previous}".format(
                title=_('Rename User Results'),
                message=self.rename_user(username_old, username_new),
                message_previous=self.msg,
            )

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

        # Try the data dir, then try to find it in the git import dir
        if not gdir.exists():
            gdir = path(git_import.GIT_REPO_DIR) / cdir
            if not gdir.exists():
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

    def get_course_from_git(self, gitloc, branch):
        """This downloads and runs the checks for importing a course in git"""

        if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
                gitloc.startswith('https:') or gitloc.startswith('git:')):
            return _("The git repo location should end with '.git', "
                     "and be a valid url")

        if self.is_using_mongo:
            return self.import_mongo_course(gitloc, branch)

        return self.import_xml_course(gitloc, branch)

    def import_mongo_course(self, gitloc, branch):
        """
        Imports course using management command and captures logging output
        at debug level for display in template
        """

        msg = u''

        log.debug('Adding course using git repo %s', gitloc)

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
        msg += u"<pre>{0}</pre>".format(escape(ret))
        return msg

    def import_xml_course(self, gitloc, branch):
        """Imports a git course into the XMLModuleStore"""

        msg = u''
        if not getattr(settings, 'GIT_IMPORT_WITH_XMLMODULESTORE', False):
            # Translators: "GIT_IMPORT_WITH_XMLMODULESTORE" is a variable name.
            # "XMLModuleStore" and "MongoDB" are database systems. You should not
            # translate these names.
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
                     'your url. Output was: {0!r}').format(ex.output)

        msg += u'<pre>{0}</pre>'.format(cmd_output)
        if not os.path.exists(gdir):
            msg += _('Failed to clone repository to {directory_name}').format(directory_name=gdir)
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
                  '{branch_name}').format(branch_name=branch))

        self.def_ms.try_load_course(os.path.abspath(gdir))
        errlog = self.def_ms.errored_courses.get(cdir, '')
        if errlog:
            msg += u'<hr width="50%"><pre>{0}</pre>'.format(escape(errlog))
        else:
            course = self.def_ms.courses[os.path.abspath(gdir)]
            msg += _('Loaded course {course_name}<br/>Errors:').format(
                course_name="{} {}".format(cdir, course.display_name)
            )
            errors = self.def_ms.get_course_errors(course.id)
            if not errors:
                msg += u'None'
            else:
                msg += u'<ul>'
                for (summary, err) in errors:
                    msg += u'<li><pre>{0}: {1}</pre></li>'.format(escape(summary),
                                                                  escape(err))
                msg += u'</ul>'

        return msg

    def make_datatable(self):
        """Creates course information datatable"""

        data = []

        for course in self.get_courses():
            gdir = course.id.course
            data.append([course.display_name, course.id.to_deprecated_string()]
                        + self.git_info_for_course(gdir))

        return dict(header=[_('Course Name'),
                            _('Directory/ID'),
                            # Translators: "Git Commit" is a computer command; see http://gitref.org/basic/#commit
                            _('Git Commit'),
                            _('Last Change'),
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

        courses = {course.id: course for course in self.get_courses()}
        if action == 'add_course':
            gitloc = request.POST.get('repo_location', '').strip().replace(' ', '').replace(';', '')
            branch = request.POST.get('repo_branch', '').strip().replace(' ', '').replace(';', '')
            self.msg += self.get_course_from_git(gitloc, branch)

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
                    self.msg += _(
                        'Error - cannot get course with ID {0}<br/><pre>{1}</pre>'
                    ).format(
                        course_key,
                        escape(str(err))
                    )

            is_xml_course = (modulestore().get_modulestore_type(course_key) == ModuleStoreEnum.Type.xml)
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
                self.def_ms.delete_course(course.id, request.user.id)
                # don't delete user permission groups, though
                self.msg += \
                    u"<font color='red'>{0} {1} = {2} ({3})</font>".format(
                        _('Deleted'), course.location.to_deprecated_string(), course.id.to_deprecated_string(), course.display_name)

        context = {
            'datatable': self.make_datatable(),
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

        for course in self.get_courses():
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

            for course in self.get_courses():
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

        page_size = 10

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
            cilset = CourseImportLog.objects.order_by('-created')
        else:
            try:
                course = get_course_by_id(course_id)
            except Exception:
                log.info('Cannot find course %s', course_id)
                raise Http404

            # Allow only course team, instructors, and staff
            if not (request.user.is_staff or
                    CourseInstructorRole(course.id).has_user(request.user) or
                    CourseStaffRole(course.id).has_user(request.user)):
                raise Http404
            log.debug('course_id=%s', course_id)
            cilset = CourseImportLog.objects.filter(
                course_id=course_id
            ).order_by('-created')
            log.debug('cilset length=%s', len(cilset))

        # Paginate the query set
        paginator = Paginator(cilset, page_size)
        try:
            logs = paginator.page(request.GET.get('page'))
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            # If the page is too high or low
            given_page = int(request.GET.get('page'))
            page = min(max(1, given_page), paginator.num_pages)
            logs = paginator.page(page)

        mdb.disconnect()
        context = {
            'logs': logs,
            'course_id': course_id.to_deprecated_string() if course_id else None,
            'error_msg': error_msg,
            'page_size': page_size
        }

        return render_to_response(self.template_name, context)


class MgmtCommands(SysadminDashboardView):
    """
    Render views for management commands
    """

    # This decorator is for the regenerate_user command, but affects all sysadmin
    # management commands
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(MgmtCommands, self).dispatch(*args, **kwargs)

    def get(self, request):
        """
        Displays the view for the management commands tab
        """

        if not request.user.is_superuser:
            raise Http404

        context = {
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'mgmt_commands': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """
        Handles a post request containing data to run a management command
        """

        if not request.user.is_superuser:
            raise Http404

        command_name, kwargs, args = self.parse_parameters(request.POST.copy())
        client_stdout, client_stderr, client_error = self.execute_command_and_capture_output(command_name, *args, **kwargs)

        log.info(client_stdout)
        log.error(client_stderr)

        response = {
            'stdout': client_stdout,
            'stderr': client_stderr,
        }
        if client_error is not None:
            response['error'] = client_error

        return JsonResponse(response)

    def execute_command_and_capture_output(self, command, *args, **kwargs):
        """
        Executes the specified command with the given args and kwargs, and returns the console output
        :param command:
        :param args:
        :param kwargs:
        :return: client_stdout, client_stderr, client_error
        """
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        sys.stdout = stdout_buffer = StringIO.StringIO()
        sys.stderr = stderr_buffer = StringIO.StringIO()

        client_error = None
        try:
            call_command(command, *args, **kwargs)
        except SystemExit:
            client_error = _('Command failed')
        except Exception as error:
            client_error = unicode(error)

        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        stdout_buffer.seek(0)
        stderr_buffer.seek(0)

        client_stdout = stdout_buffer.read()
        client_stderr = stderr_buffer.read()
        return client_stdout, client_stderr, client_error

    def parse_parameters(self, parameters):
        """
        Parses the list of parameters from the ExecuteCommand post request
        :param params:
        :return: command_name, kwargs, args
        """
        command_name = parameters.pop('command')[0]

        kwargs = {}
        args = []
        # collect kwargs and args
        if 'args' in parameters:
            args = parameters.pop('args')
        if 'kwflags' in parameters:
            kwflags = parameters.pop('kwflags')
            for kwflag in kwflags:
                kwargs[kwflag] = None
        for kwarg in parameters:
            kwargs[kwarg] = parameters[kwarg]
        return command_name, kwargs, args


class TaskQueue(SysadminDashboardView):
    """
    This provides the ability to kill an InstructorTask.

    This is done by updating the row's task_state from "QUEUING" to "FAILURE".
    """

    def kill_task(self, row_id=None):
        """
        Kills an InstructorTask by changing it's task_state from 'QUEUING' to 'FAILURE'

        Args:
          Input: row_id (string)
        """
        if not row_id:
            return _('Must provide an ID')

        try:
            int(row_id)
        except ValueError:
            return _('ID must be an integer')

        msg = u''
        try:
            task = InstructorTask.objects.get(
                id=row_id,
                task_state__in=[
                    'QUEUING',
                    'PROGRESS',
                ],
            )
        except InstructorTask.DoesNotExist, err:
            msg = _('Cannot find task with ID {row_id} and task_state QUEUING - {error}').format(
                row_id=row_id,
                error=str(err)
            )
            return msg

        task.task_state = 'FAILURE'
        task.save()

        msg += _('Task with id {row_id} was successfully killed!').format(row_id=row_id)
        return msg

    def make_datatable(self):
        """Creates InstructorTask information datatable"""

        data = []

        tasks = InstructorTask.objects.filter(
            task_state__in=[
                'QUEUING',
                'PROGRESS',
            ],
        ).order_by('id').reverse()
        for task in tasks:
            data.append(
                [
                    task.id,
                    task.course_id,
                    task.task_type,
                    task.task_state,
                ]
            )

        return dict(
            header=[
                _('ID'),
                _('Course ID'),
                _('Task Type'),
                _('Task State'),
            ],
            title=_('List of Tasks'),
            data=data,
        )

    def get(self, request):
        """
        Displays form allowing admin to kill an InstructorTask.

        Args:
          Input: request (Django Request object)
        """
        if not request.user.is_staff:
            raise Http404

        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'task_queue': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """
        Handle actions on page Task Queue page.

        Args:
          Input: request (Django Request object)
        """

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {},
                                 page='task_queue_sysdashboard')

        if action == 'kill_task':
            row_id = request.POST.get('row_id', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />{2}'.format(
                _('Kill Task Results'),
                self.kill_task(row_id), self.msg)

        else:
            self.msg = u'<p>{0}</p><hr />'.format(
                _('Unrecognized action'),
            )

        context = {
            'datatable': self.datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'task_queue': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)
