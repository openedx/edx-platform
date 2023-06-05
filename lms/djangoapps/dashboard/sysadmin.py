"""
This module creates a sysadmin dashboard for managing and viewing
courses.
"""


import json
import logging
import os
import subprocess

import mongoengine
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView
from opaque_keys.edx.keys import CourseKey
from path import Path as path
from six import StringIO, text_type

import lms.djangoapps.dashboard.git_import as git_import
from common.djangoapps.track import views as track_views
from lms.djangoapps.dashboard.git_import import GitImportError
from lms.djangoapps.dashboard.models import CourseImportLog
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.courseware.courses import get_course_by_id
from openedx.core.djangolib.markup import HTML
from common.djangoapps.student.models import CourseEnrollment, Registration, UserProfile
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.django import modulestore

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


class Users(SysadminDashboardView):
    """
    The status view provides Web based user management, a listing of
    courses loaded, and user statistics
    """

    def create_user(self, uname, name, password=None):
        """ Creates a user """

        if not uname:
            return _('Must provide username')
        if not name:
            return _('Must provide full name')

        msg = u''
        if not password:
            return _('Password must be supplied')

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
            msg += _(u'Oops, failed to create user {user}, {error}').format(
                user=user,
                error="IntegrityError"
            )
            return msg

        reg = Registration()
        reg.register(user)

        profile = UserProfile(user=user)
        profile.name = name
        profile.save()

        msg += _(u'User {user} created successfully!').format(user=user)
        return msg

    def delete_user(self, uname):
        """Deletes a user from django auth"""

        if not uname:
            return _('Must provide username')
        if '@' in uname:
            try:
                user = User.objects.get(email=uname)
            except User.DoesNotExist as err:
                msg = _(u'Cannot find user with email address {email_addr}').format(email_addr=uname)
                return msg
        else:
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist as err:
                msg = _(u'Cannot find user with username {username} - {error}').format(
                    username=uname,
                    error=str(err)
                )
                return msg
        user.delete()
        return _(u'Deleted user {username}').format(username=uname)

    def make_datatable(self):
        """
        Build the datatable for this view
        """
        datatable = {
            'header': [
                _('Statistic'),
                _('Value'),
            ],
            'title': _('Site statistics'),
            'data': [
                [
                    _('Total number of users'),
                    User.objects.all().count(),
                ],
            ],
        }
        return datatable

    def get(self, request):
        if not request.user.is_staff:
            raise Http404
        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle various actions available on page"""

        if not request.user.is_staff:
            raise Http404
        action = request.POST.get('action', '')
        track_views.server_track(request, action, {}, page='user_sysdashboard')

        if action == 'create_user':
            uname = request.POST.get('student_uname', '').strip()
            name = request.POST.get('student_fullname', '').strip()
            password = request.POST.get('student_password', '').strip()
            self.msg = HTML(u'<h4>{0}</h4><p>{1}</p><hr />{2}').format(
                _('Create User Results'),
                self.create_user(uname, name, password), self.msg)
        elif action == 'del_user':
            uname = request.POST.get('student_uname', '').strip()
            self.msg = HTML(u'<h4>{0}</h4><p>{1}</p><hr />{2}').format(
                _('Delete User Results'), self.delete_user(uname), self.msg)
        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
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
            git_repo_dir = getattr(settings, 'GIT_REPO_DIR', git_import.DEFAULT_GIT_REPO_DIR)
            gdir = path(git_repo_dir) / cdir
            if not gdir.exists():
                return info

        cmd = ['git', 'log', '-1',
               u'--format=format:{ "commit": "%H", "author": "%an %ae", "date": "%ad"}', ]
        try:
            output_json = json.loads(subprocess.check_output(cmd, cwd=gdir).decode('utf-8'))
            info = [output_json['commit'],
                    output_json['date'],
                    output_json['author'], ]
        except OSError as error:
            log.warning(text_type(u"Error fetching git data: %s - %s"), text_type(cdir), text_type(error))
        except (ValueError, subprocess.CalledProcessError):
            pass

        return info

    def get_course_from_git(self, gitloc, branch):
        """This downloads and runs the checks for importing a course in git"""

        if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
                gitloc.startswith('https:') or gitloc.startswith('git:')):
            return _("The git repo location should end with '.git', "
                     "and be a valid url")

        return self.import_mongo_course(gitloc, branch)

    def import_mongo_course(self, gitloc, branch):
        """
        Imports course using management command and captures logging output
        at debug level for display in template
        """

        msg = u''

        log.debug(u'Adding course using git repo %s', gitloc)

        # Grab logging output for debugging imports
        output = StringIO()
        import_log_handler = logging.StreamHandler(output)
        import_log_handler.setLevel(logging.DEBUG)

        logger_names = ['xmodule.modulestore.xml_importer',
                        'lms.djangoapps.dashboard.git_import',
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

        msg = HTML(u"<h4 style='color:{0}'>{1}</h4>").format(color, msg_header)
        msg += HTML(u"<pre>{0}</pre>").format(escape(ret))
        return msg

    def make_datatable(self, courses=None):
        """Creates course information datatable"""

        data = []
        courses = courses or self.get_courses()
        for course in courses:
            gdir = course.id.course
            data.append([course.display_name, text_type(course.id)]
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
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle all actions from courses view"""

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get('action', '')
        track_views.server_track(request, action, {},
                                 page='courses_sysdashboard')

        courses = {course.id: course for course in self.get_courses()}
        if action == 'add_course':
            gitloc = request.POST.get('repo_location', '').strip().replace(' ', '').replace(';', '')
            branch = request.POST.get('repo_branch', '').strip().replace(' ', '').replace(';', '')
            self.msg += self.get_course_from_git(gitloc, branch)

        elif action == 'del_course':
            course_id = request.POST.get('course_id', '').strip()
            course_key = CourseKey.from_string(course_id)
            course_found = False
            if course_key in courses:
                course_found = True
                course = courses[course_key]
            else:
                try:
                    course = get_course_by_id(course_key)
                    course_found = True
                except Exception as err:   # pylint: disable=broad-except
                    self.msg += _(
                        HTML(u'Error - cannot get course with ID {0}<br/><pre>{1}</pre>')
                    ).format(
                        course_key,
                        escape(str(err))
                    )

            if course_found:
                # delete course that is stored with mongodb backend
                self.def_ms.delete_course(course.id, request.user.id)
                # don't delete user permission groups, though
                self.msg += \
                    HTML(u"<font color='red'>{0} {1} = {2} ({3})</font>").format(
                        _('Deleted'), text_type(course.location), text_type(course.id), course.display_name)

        context = {
            'datatable': self.make_datatable(list(courses.values())),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'courses': 'active-section'},
        }
        return render_to_response(self.template_name, context)


class Staffing(SysadminDashboardView):
    """
    The status view provides a view of staffing and enrollment in
    courses.
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
        }
        return render_to_response(self.template_name, context)


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
            course_id = CourseKey.from_string(course_id)

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
            # Allow only course team, instructors, and staff
            if not (request.user.is_staff or
                    CourseInstructorRole(course_id).has_user(request.user) or
                    CourseStaffRole(course_id).has_user(request.user)):
                raise Http404
            log.debug('course_id=%s', course_id)
            cilset = CourseImportLog.objects.filter(
                course_id=course_id
            ).order_by('-created')
            log.debug(u'cilset length=%s', len(cilset))

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

        mdb.close()
        context = {
            'logs': logs,
            'course_id': text_type(course_id) if course_id else None,
            'error_msg': error_msg,
            'page_size': page_size
        }

        return render_to_response(self.template_name, context)
