# ======== Instructor views =============================================================================

from collections import defaultdict
import csv
import json
import logging
import os
import requests
import urllib

from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from courseware import grades
from courseware.access import (has_access, get_access_group_name,
                               course_beta_test_group_name)
from courseware.courses import get_course_with_access
from django_comment_client.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)
from django_comment_client.utils import has_forum_access
from psychometrics import psychoanalyze
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
import track.views

from .offline_gradecalc import student_grades, offline_grades_available

log = logging.getLogger(__name__)

template_imports = {'urllib': urllib}

# internal commands for managing forum roles:
FORUM_ROLE_ADD = 'add'
FORUM_ROLE_REMOVE = 'remove'

@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard(request, course_id):
    """Display the instructor dashboard for a course."""
    course = get_course_with_access(request.user, course_id, 'staff')

    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists

    forum_admin_access = has_forum_access(request.user, course_id, FORUM_ROLE_ADMINISTRATOR)

    msg = ''
    problems = []
    plots = []

    # the instructor dashboard page is modal: grades, psychometrics, admin
    # keep that state in request.session (defaults to grades mode)
    idash_mode = request.POST.get('idash_mode','')
    if idash_mode:
        request.session['idash_mode'] = idash_mode
    else:
        idash_mode = request.session.get('idash_mode','Grades')

    def escape(s):
        """escape HTML special characters in string"""
        return str(s).replace('<', '&lt;').replace('>', '&gt;')

    # assemble some course statistics for output to instructor
    datatable = {'header': ['Statistic', 'Value'],
                 'title': 'Course Statistics At A Glance',
                 }
    data = [['# Enrolled', CourseEnrollment.objects.filter(course_id=course_id).count()]]
    data += compute_course_stats(course).items()
    if request.user.is_staff:
        data.append(['metadata', escape(str(course.metadata))])
    datatable['data'] = data

    def return_csv(fn, datatable, fp=None):
        if fp is None:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename={0}'.format(fn)
        else:
            response = fp
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
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
            group = Group(name=grpname)     # create the group
            group.save()

    def get_beta_group(course):
        """
        Get the group for beta testers of course.
        """
        # Not using get_group because there is no access control action called
        # 'beta', so adding it to get_access_group_name doesn't really make
        # sense.
        name = course_beta_test_group_name(course.location)
        (group, created) = Group.objects.get_or_create(name=name)
        return group

    # process actions from form POST
    action = request.POST.get('action', '')
    use_offline = request.POST.get('use_offline_grades',False)

    if settings.MITX_FEATURES['ENABLE_MANUAL_GIT_RELOAD']:
        if 'GIT pull' in action:
            data_dir = course.metadata['data_dir']
            log.debug('git pull {0}'.format(data_dir))
            gdir = settings.DATA_DIR / data_dir
            if not os.path.exists(gdir):
                msg += "====> ERROR in gitreload - no such directory {0}".format(gdir)
            else:
                cmd = "cd {0}; git reset --hard HEAD; git clean -f -d; git pull origin; chmod g+w course.xml".format(gdir)
                msg += "git pull on {0}:<p>".format(data_dir)
                msg += "<pre>{0}</pre></p>".format(escape(os.popen(cmd).read()))
                track.views.server_track(request, 'git pull {0}'.format(data_dir), {}, page='idashboard')

        if 'Reload course' in action:
            log.debug('reloading {0} ({1})'.format(course_id, course))
            try:
                data_dir = course.metadata['data_dir']
                modulestore().try_load_course(data_dir)
                msg += "<br/><p>Course reloaded from {0}</p>".format(data_dir)
                track.views.server_track(request, 'reload {0}'.format(data_dir), {}, page='idashboard')
                course_errors = modulestore().get_item_errors(course.location)
                msg += '<ul>'
                for cmsg, cerr in course_errors:
                    msg += "<li>{0}: <pre>{1}</pre>".format(cmsg,escape(cerr))
                msg += '</ul>'
            except Exception as err:
                msg += '<br/><p>Error: {0}</p>'.format(escape(err))

    if action == 'Dump list of enrolled students' or action=='List enrolled students':
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=False, use_offline=use_offline)
        datatable['title'] = 'List of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'list-students', {}, page='idashboard')

    elif 'Dump Grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True, use_offline=use_offline)
        datatable['title'] = 'Summary Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'dump-grades', {}, page='idashboard')

    elif 'Dump all RAW grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True,
                                                   get_raw_scores=True, use_offline=use_offline)
        datatable['title'] = 'Raw Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'dump-grades-raw', {}, page='idashboard')

    elif 'Download CSV of all student grades' in action:
        track.views.server_track(request, 'dump-grades-csv', {}, page='idashboard')
        return return_csv('grades_{0}.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id, use_offline=use_offline))

    elif 'Download CSV of all RAW grades' in action:
        track.views.server_track(request, 'dump-grades-csv-raw', {}, page='idashboard')
        return return_csv('grades_{0}_raw.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id, get_raw_scores=True, use_offline=use_offline))

    elif 'Download CSV of answer distributions' in action:
        track.views.server_track(request, 'dump-answer-dist-csv', {}, page='idashboard')
        return return_csv('answer_dist_{0}.csv'.format(course_id), get_answers_distribution(request, course_id))

    #----------------------------------------
    # export grades to remote gradebook

    elif action=='List assignments available in remote gradebook':
        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-assignments')
        msg += msg2

    elif action=='List assignments available for this course':
        log.debug(action)
        allgrades = get_student_grade_summary_data(request, course, course_id, get_grades=True, use_offline=use_offline)

        assignments = [[x] for x in allgrades['assignments']]
        datatable = {'header': ['Assignment Name']}
        datatable['data'] = assignments
        datatable['title'] = action

        msg += 'assignments=<pre>%s</pre>' % assignments

    elif action=='List enrolled students matching remote gradebook':
        stud_data = get_student_grade_summary_data(request, course, course_id, get_grades=False, use_offline=use_offline)
        msg2, rg_stud_data = _do_remote_gradebook(request.user, course, 'get-membership')
        datatable = {'header': ['Student  email', 'Match?']}
        rg_students = [ x['email'] for x in rg_stud_data['retdata'] ]
        def domatch(x):
            return '<font color="green">yes</font>' if x.email in rg_students else '<font color="red">No</font>'
        datatable['data'] = [[x.email, domatch(x)] for x in stud_data['students']]
        datatable['title'] = action

    elif action in ['Display grades for assignment', 'Export grades for assignment to remote gradebook',
                    'Export CSV file of grades for assignment']:

        log.debug(action)
        datatable = {}
        aname = request.POST.get('assignment_name','')
        if not aname:
            msg += "<font color='red'>Please enter an assignment name</font>"
        else:
            allgrades = get_student_grade_summary_data(request, course, course_id, get_grades=True, use_offline=use_offline)
            if aname not in allgrades['assignments']:
                msg += "<font color='red'>Invalid assignment name '%s'</font>" % aname
            else:
                aidx = allgrades['assignments'].index(aname)
                datatable = {'header': ['External email', aname]}
                datatable['data'] = [[x.email, x.grades[aidx]] for x in allgrades['students']]
                datatable['title'] = 'Grades for assignment "%s"' % aname

                if 'Export CSV' in action:
                    # generate and return CSV file
                    return return_csv('grades %s.csv' % aname, datatable)

                elif 'remote gradebook' in action:
                    fp = StringIO()
                    return_csv('', datatable, fp=fp)
                    fp.seek(0)
                    files = {'datafile': fp}
                    msg2, dataset = _do_remote_gradebook(request.user, course, 'post-grades', files=files)
                    msg += msg2


    #----------------------------------------
    # Admin

    elif 'List course staff' in action:
        group = get_staff_group(course)
        msg += 'Staff group = {0}'.format(group.name)
        datatable = _group_members_table(group, "List of Staff", course_id)
        track.views.server_track(request, 'list-staff', {}, page='idashboard')

    elif 'List course instructors' in action and request.user.is_staff:
        group = get_instructor_group(course)
        msg += 'Instructor group = {0}'.format(group.name)
        log.debug('instructor grp={0}'.format(group.name))
        uset = group.user_set.all()
        datatable = {'header': ['Username', 'Full name']}
        datatable['data'] = [[x.username, x.profile.name] for x in uset]
        datatable['title'] = 'List of Instructors in course {0}'.format(course_id)
        track.views.server_track(request, 'list-instructors', {}, page='idashboard')

    elif action == 'Add course staff':
        uname = request.POST['staffuser']
        group = get_staff_group(course)
        msg += add_user_to_group(request, uname, group, 'staff', 'staff')

    elif action == 'Add instructor' and request.user.is_staff:
        uname = request.POST['instructor']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
            user = None
        if user is not None:
            group = get_instructor_group(course)
            msg += '<font color="green">Added {0} to instructor group = {1}</font>'.format(user, group.name)
            log.debug('staffgrp={0}'.format(group.name))
            user.groups.add(group)
            track.views.server_track(request, 'add-instructor {0}'.format(user), {}, page='idashboard')

    elif action == 'Remove course staff':
        uname = request.POST['staffuser']
        group = get_staff_group(course)
        msg += remove_user_from_group(request, uname, group, 'staff', 'staff')

    elif action == 'Remove instructor' and request.user.is_staff:
        uname = request.POST['instructor']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
            user = None
        if user is not None:
            group = get_instructor_group(course)
            msg += '<font color="green">Removed {0} from instructor group = {1}</font>'.format(user, group.name)
            log.debug('instructorgrp={0}'.format(group.name))
            user.groups.remove(group)
            track.views.server_track(request, 'remove-instructor {0}'.format(user), {}, page='idashboard')

    #----------------------------------------
    # Group management

    elif 'List beta testers' in action:
        group = get_beta_group(course)
        msg += 'Beta test group = {0}'.format(group.name)
        datatable = _group_members_table(group, "List of beta_testers", course_id)
        track.views.server_track(request, 'list-beta-testers', {}, page='idashboard')

    elif action == 'Add beta testers':
        uname = request.POST['betausers']
        group = get_beta_group(course)
        msg += add_user_to_group(request, uname, group, 'beta testers', 'beta-tester')

    elif action == 'Remove beta testers':
        uname = request.POST['betausers']
        group = get_beta_group(course)
        msg += remove_user_from_group(request, uname, group, 'beta testers', 'beta-tester')

    #----------------------------------------
    # forum administration

    elif action == 'List course forum admins':
        rolename = FORUM_ROLE_ADMINISTRATOR
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, 'list-{0}'.format(rolename), {}, page='idashboard')


    elif action == 'Remove forum admin':
        uname = request.POST['forumadmin']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_REMOVE)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_REMOVE, uname, FORUM_ROLE_ADMINISTRATOR, course_id),
                                 {}, page='idashboard')

    elif action == 'Add forum admin':
        uname = request.POST['forumadmin']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_ADD)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_ADD, uname, FORUM_ROLE_ADMINISTRATOR, course_id),
                                 {}, page='idashboard')

    elif action == 'List course forum moderators':
        rolename = FORUM_ROLE_MODERATOR
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, 'list-{0}'.format(rolename), {}, page='idashboard')

    elif action == 'Remove forum moderator':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_MODERATOR, FORUM_ROLE_REMOVE)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_REMOVE, uname, FORUM_ROLE_MODERATOR, course_id),
                                 {}, page='idashboard')

    elif action == 'Add forum moderator':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_MODERATOR, FORUM_ROLE_ADD)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_ADD, uname, FORUM_ROLE_MODERATOR, course_id),
                                 {}, page='idashboard')

    elif action == 'List course forum community TAs':
        rolename = FORUM_ROLE_COMMUNITY_TA
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, 'list-{0}'.format(rolename), {}, page='idashboard')

    elif action == 'Remove forum community TA':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_REMOVE)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_REMOVE, uname, FORUM_ROLE_COMMUNITY_TA, course_id),
                                 {}, page='idashboard')

    elif action == 'Add forum community TA':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_ADD)
        track.views.server_track(request, '{0} {1} as {2} for {3}'.format(FORUM_ROLE_ADD, uname, FORUM_ROLE_COMMUNITY_TA, course_id),
                                 {}, page='idashboard')

    #----------------------------------------
    # enrollment

    elif action == 'List students who may enroll but may not have yet signed up':
        ceaset = CourseEnrollmentAllowed.objects.filter(course_id=course_id)
        datatable = {'header': ['StudentEmail']}
        datatable['data'] = [[x.email] for x in ceaset]
        datatable['title'] = action

    elif action == 'Enroll student':

        student = request.POST.get('enstudent','')
        ret = _do_enroll_students(course, course_id, student)
        datatable = ret['datatable']

    elif action == 'Un-enroll student':

        student = request.POST.get('enstudent','')
        datatable = {}
        isok = False
        cea = CourseEnrollmentAllowed.objects.filter(course_id=course_id, email=student)
        if cea:
            cea.delete()
            msg += "Un-enrolled student with email '%s'" % student
            isok = True
        try:
            nce = CourseEnrollment.objects.get(user=User.objects.get(email=student), course_id=course_id)
            nce.delete()
            msg += "Un-enrolled student with email '%s'" % student
        except Exception as err:
            if not isok:
                msg += "Error!  Failed to un-enroll student with email '%s'\n" % student
                msg += str(err) + '\n'

    elif action == 'Un-enroll ALL students':

        ret = _do_enroll_students(course, course_id, '', overload=True)
        datatable = ret['datatable']

    elif action == 'Enroll multiple students':

        students = request.POST.get('enroll_multiple','')
        ret = _do_enroll_students(course, course_id, students)
        datatable = ret['datatable']

    elif action == 'List sections available in remote gradebook':

        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-sections')
        msg += msg2

    elif action in ['List students in section in remote gradebook',
                    'Overload enrollment list using remote gradebook',
                    'Merge enrollment list with remote gradebook']:

        section = request.POST.get('gradebook_section','')
        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-membership', dict(section=section) )
        msg += msg2

        if not 'List' in action:
            students = ','.join([x['email'] for x in datatable['retdata']])
            overload = 'Overload' in action
            ret = _do_enroll_students(course, course_id, students, overload=overload)
            datatable = ret['datatable']


    #----------------------------------------
    # psychometrics

    elif action == 'Generate Histogram and IRT Plot':
        problem = request.POST['Problem']
        nmsg, plots = psychoanalyze.generate_plots_for_problem(problem)
        msg += nmsg
        track.views.server_track(request, 'psychometrics {0}'.format(problem), {}, page='idashboard')

    if idash_mode=='Psychometrics':
        problems = psychoanalyze.problems_with_psychometric_data(course_id)


    #----------------------------------------
    # offline grades?

    if use_offline:
        msg += "<br/><font color='orange'>Grades from %s</font>" % offline_grades_available(course_id)

    #----------------------------------------
    # context for rendering

    context = {'course': course,
               'staff_access': True,
               'admin_access': request.user.is_staff,
               'instructor_access': instructor_access,
               'forum_admin_access': forum_admin_access,
               'datatable': datatable,
               'msg': msg,
               'modeflag': {idash_mode: 'selectedmode'},
               'problems': problems,		# psychometrics
               'plots': plots,			# psychometrics
               'course_errors': modulestore().get_item_errors(course.location),
               'djangopid' : os.getpid(),
               'mitx_version' : getattr(settings,'MITX_VERSION_STRING',''),
               'offline_grade_log' : offline_grades_available(course_id),
               }

    return render_to_response('courseware/instructor_dashboard.html', context)


def _do_remote_gradebook(user, course, action, args=None, files=None):
    '''
    Perform remote gradebook action.  Returns msg, datatable.
    '''
    rg = course.metadata.get('remote_gradebook','')
    if not rg:
        msg = "No remote gradebook defined in course metadata"
        return msg, {}

    rgurl = settings.MITX_FEATURES.get('REMOTE_GRADEBOOK_URL','')
    if not rgurl:
        msg = "No remote gradebook url defined in settings.MITX_FEATURES"
        return msg, {}

    rgname = rg.get('name','')
    if not rgname:
        msg = "No gradebook name defined in course remote_gradebook metadata"
        return msg, {}

    if args is None:
        args = {}
    data = dict(submit=action, gradebook=rgname, user=user.email)
    data.update(args)

    try:
        resp = requests.post(rgurl, data=data, verify=False, files=files)
        retdict = json.loads(resp.content)
    except Exception as err:
        msg = "Failed to communicate with gradebook server at %s<br/>" % rgurl
        msg += "Error: %s" % err
        msg += "<br/>resp=%s" % resp.content
        msg += "<br/>data=%s" % data
        return msg, {}

    msg = '<pre>%s</pre>' % retdict['msg'].replace('\n','<br/>')
    retdata = retdict['data']	# a list of dicts

    if retdata:
        datatable = {'header': retdata[0].keys()}
        datatable['data'] = [x.values() for x in retdata]
        datatable['title'] = 'Remote gradebook response for %s' % action
        datatable['retdata'] = retdata
    else:
        datatable = {}

    return msg, datatable

def _list_course_forum_members(course_id, rolename, datatable):
    """
    Fills in datatable with forum membership information, for a given role,
    so that it will be displayed on instructor dashboard.

      course_ID = the ID string for a course
      rolename = one of "Administrator", "Moderator", "Community TA"

    Returns message status string to append to displayed message, if role is unknown.
    """
    # make sure datatable is set up properly for display first, before checking for errors
    datatable['header'] = ['Username', 'Full name', 'Roles']
    datatable['title'] = 'List of Forum {0}s in course {1}'.format(rolename, course_id)
    datatable['data'] = [];
    try:
        role = Role.objects.get(name=rolename, course_id=course_id)
    except Role.DoesNotExist:
        return '<font color="red">Error: unknown rolename "{0}"</font>'.format(rolename)
    uset = role.users.all().order_by('username')
    msg = 'Role = {0}'.format(rolename)
    log.debug('role={0}'.format(rolename))
    datatable['data'] = [[x.username, x.profile.name, ', '.join([r.name for r in x.roles.filter(course_id=course_id).order_by('name')])] for x in uset]
    return msg


def _update_forum_role_membership(uname, course, rolename, add_or_remove):
    '''
    Supports adding a user to a course's forum role

      uname = username string for user
      course = course object
      rolename = one of "Administrator", "Moderator", "Community TA"
      add_or_remove = one of "add" or "remove"

    Returns message status string to append to displayed message,  Status is returned if user
    or role is unknown, or if entry already exists when adding, or if entry doesn't exist when removing.
    '''
    # check that username and rolename are valid:
    try:
        user = User.objects.get(username=uname)
    except User.DoesNotExist:
        return '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
    try:
        role = Role.objects.get(name=rolename, course_id=course.id)
    except Role.DoesNotExist:
        return '<font color="red">Error: unknown rolename "{0}"</font>'.format(rolename)

    # check whether role already has the specified user:
    alreadyexists = role.users.filter(username=uname).exists()
    msg = ''
    log.debug('rolename={0}'.format(rolename))
    if add_or_remove == FORUM_ROLE_REMOVE:
        if not alreadyexists:
            msg ='<font color="red">Error: user "{0}" does not have rolename "{1}", cannot remove</font>'.format(uname, rolename)
        else:
            user.roles.remove(role)
            msg = '<font color="green">Removed "{0}" from "{1}" forum role = "{2}"</font>'.format(user, course.id, rolename)
    else:
        if alreadyexists:
            msg = '<font color="red">Error: user "{0}" already has rolename "{1}", cannot add</font>'.format(uname, rolename)
        else:
            if (rolename == FORUM_ROLE_ADMINISTRATOR and not has_access(user, course, 'staff')):
                msg = '<font color="red">Error: user "{0}" should first be added as staff before adding as a forum administrator, cannot add</font>'.format(uname)
            else:
                user.roles.add(role)
                msg = '<font color="green">Added "{0}" to "{1}" forum role = "{2}"</font>'.format(user, course.id, rolename)

    return msg

def _group_members_table(group, title, course_id):
    """
    Return a data table of usernames and names of users in group_name.

    Arguments:
        group -- a django group.
        title -- a descriptive title to show the user

    Returns:
        a dictionary with keys
        'header': ['Username', 'Full name'],
        'data': [[username, name] for all users]
        'title': "{title} in course {course}"
    """
    uset = group.user_set.all()
    datatable = {'header': ['Username', 'Full name']}
    datatable['data'] = [[x.username, x.profile.name] for x in uset]
    datatable['title'] = '{0} in course {1}'.format(title, course_id)
    return datatable

def add_user_to_group(request, username_or_email, group, group_title, event_name):
    """
    Look up the given user by username (if no '@') or email (otherwise), and add them to group.

    Arguments:
       request: django request--used for tracking log
       username_or_email: who to add.  Decide if it's an email by presense of an '@'
       group: django group object
       group_title: what to call this group in messages to user--e.g. "beta-testers".
       event_name: what to call this event when logging to tracking logs.

    Returns:
       html to insert in the message field
    """
    user = None
    try:
        if '@' in username_or_email:
            user = User.objects.get(email=username_or_email)
        else:
            user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        msg = '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
        user = None

    if user is not None:
        msg = '<font color="green">Added {0} to {1} group = {2}</font>'.format(user, group_title, group.name)
        user.groups.add(group)
        track.views.server_track(request, 'add-{0} {1}'.format(event_name, user), {}, page='idashboard')

    return msg

def remove_user_from_group(request, username_or_email, group, group_title, event_name):
    """
    Look up the given user by username (if no '@') or email (otherwise), and remove them from group.

    Arguments:
       request: django request--used for tracking log
       username_or_email: who to remove.  Decide if it's an email by presense of an '@'
       group: django group object
       group_title: what to call this group in messages to user--e.g. "beta-testers".
       event_name: what to call this event when logging to tracking logs.

    Returns:
       html to insert in the message field
    """
    user = None
    try:
        if '@' in username_or_email:
            user = User.objects.get(email=username_or_email)
        else:
            user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        msg = '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
        user = None

    if user is not None:
        msg = '<font color="green">Removed {0} from {1} group = {2}</font>'.format(user, group_title, group.name)
        user.groups.remove(group)
        track.views.server_track(request, 'remove-{0} {1}'.format(event_name, user), {}, page='idashboard')

    return msg


def get_student_grade_summary_data(request, course, course_id, get_grades=True, get_raw_scores=False, use_offline=False):
    '''
    Return data arrays with student identity and grades for specified course.

    course = CourseDescriptor
    course_id = course ID

    Note: both are passed in, only because instructor_dashboard already has them already.

    returns datatable = dict(header=header, data=data)
    where

    header = list of strings labeling the data fields
    data = list (one per student) of lists of data corresponding to the fields

    If get_raw_scores=True, then instead of grade summaries, the raw grades for all graded modules are returned.

    '''
    enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).prefetch_related("groups").order_by('username')

    header = ['ID', 'Username', 'Full Name', 'edX email', 'External email']
    assignments = []
    if get_grades and enrolled_students.count() > 0:
        # just to construct the header
        gradeset = student_grades(enrolled_students[0], request, course, keep_raw_scores=get_raw_scores, use_offline=use_offline)
        # log.debug('student {0} gradeset {1}'.format(enrolled_students[0], gradeset))
        if get_raw_scores:
            assignments += [score.section for score in gradeset['raw_scores']]
        else:
            assignments += [x['label'] for x in gradeset['section_breakdown']]
    header += assignments

    datatable = {'header': header, 'assignments': assignments, 'students': enrolled_students}
    data = []

    for student in enrolled_students:
        datarow = [ student.id, student.username, student.profile.name, student.email ]
        try:
            datarow.append(student.externalauthmap.external_email)
        except:	# ExternalAuthMap.DoesNotExist
            datarow.append('')

        if get_grades:
            gradeset = student_grades(student, request, course, keep_raw_scores=get_raw_scores, use_offline=use_offline)
            log.debug('student={0}, gradeset={1}'.format(student,gradeset))
            if get_raw_scores:
                # TODO (ichuang) encode Score as dict instead of as list, so score[0] -> score['earned']
                sgrades = [(getattr(score,'earned','') or score[0]) for score in gradeset['raw_scores']]
            else:
                sgrades = [x['percent'] for x in gradeset['section_breakdown']]
            datarow += sgrades
            student.grades = sgrades	# store in student object

        data.append(datarow)
    datatable['data'] = data
    return datatable

#-----------------------------------------------------------------------------

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def gradebook(request, course_id):
    """
    Show the gradebook for this course:
    - only displayed to course staff
    - shows students who are enrolled.
    """
    course = get_course_with_access(request.user, course_id, 'staff')

    enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).order_by('username').select_related("profile")

    # TODO (vshnayder): implement pagination.
    enrolled_students = enrolled_students[:1000]   # HACK!

    student_info = [{'username': student.username,
                     'id': student.id,
                     'email': student.email,
                     'grade_summary': student_grades(student, request, course),
                     'realname': student.profile.name,
                     }
                     for student in enrolled_students]

    return render_to_response('courseware/gradebook.html', {'students': student_info,
                                                 'course': course,
                                                 'course_id': course_id,
                                                 # Checked above
                                                 'staff_access': True, })


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def grade_summary(request, course_id):
    """Display the grade summary for a course."""
    course = get_course_with_access(request.user, course_id, 'staff')

    # For now, just a static page
    context = {'course': course,
               'staff_access': True, }
    return render_to_response('courseware/grade_summary.html', context)


#-----------------------------------------------------------------------------
# enrollment


def _do_enroll_students(course, course_id, students, overload=False):
    """Do the actual work of enrolling multiple students, presented as a string
    of emails separated by commas or returns"""

    ns = [x.split('\n') for x in students.split(',')]
    new_students = [item for sublist in ns for item in sublist]
    new_students = [str(s.strip()) for s in new_students]
    new_students_lc = [x.lower() for x in new_students]

    if '' in new_students:
        new_students.remove('')

    status = dict([x,'unprocessed'] for x in new_students)

    if overload:	# delete all but staff
        todelete = CourseEnrollment.objects.filter(course_id=course_id)
        for ce in todelete:
            if not has_access(ce.user, course, 'staff') and ce.user.email.lower() not in new_students_lc:
                status[ce.user.email] = 'deleted'
                ce.delete()
            else:
                status[ce.user.email] = 'is staff'
        ceaset = CourseEnrollmentAllowed.objects.filter(course_id=course_id)
        for cea in ceaset:
            status[cea.email] = 'removed from pending enrollment list'
        ceaset.delete()

    for student in new_students:
        try:
            user=User.objects.get(email=student)
        except User.DoesNotExist:
            # user not signed up yet, put in pending enrollment allowed table
            if CourseEnrollmentAllowed.objects.filter(email=student, course_id=course_id):
                status[student] = 'user does not exist, enrollment already allowed, pending'
                continue
            cea = CourseEnrollmentAllowed(email=student, course_id=course_id)
            cea.save()
            status[student] = 'user does not exist, enrollment allowed, pending'
            continue

        if CourseEnrollment.objects.filter(user=user, course_id=course_id):
            status[student] = 'already enrolled'
            continue
        try:
            nce = CourseEnrollment(user=user, course_id=course_id)
            nce.save()
            status[student] = 'added'
        except:
            status[student] = 'rejected'

    datatable = {'header': ['StudentEmail', 'action']}
    datatable['data'] = [[x, status[x]] for x in status]
    datatable['title'] = 'Enrollment of students'

    def sf(stat): return [x for x in status if status[x]==stat]

    data = dict(added=sf('added'), rejected=sf('rejected')+sf('exists'),
                deleted=sf('deleted'), datatable=datatable)

    return data


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def enroll_students(request, course_id):
    """Allows a staff member to enroll students in a course.

    This is a short-term hack for Berkeley courses launching fall
    2012. In the long term, we would like functionality like this, but
    we would like both the instructor and the student to agree. Right
    now, this allows any instructor to add students to their course,
    which we do not want.

    It is poorly written and poorly tested, but it's designed to be
    stripped out.
    """

    course = get_course_with_access(request.user, course_id, 'staff')
    existing_students = [ce.user.email for ce in CourseEnrollment.objects.filter(course_id=course_id)]

    new_students = request.POST.get('new_students')
    ret = _do_enroll_students(course, course_id, new_students)
    added_students = ret['added']
    rejected_students = ret['rejected']

    return render_to_response("enroll_students.html", {'course': course_id,
                                                       'existing_students': existing_students,
                                                       'added_students': added_students,
                                                       'rejected_students': rejected_students,
                                                       'debug': new_students})


#-----------------------------------------------------------------------------
# answer distribution

def get_answers_distribution(request, course_id):
    """
    Get the distribution of answers for all graded problems in the course.

    Return a dict with two keys:
    'header': a header row
    'data': a list of rows
    """
    course = get_course_with_access(request.user, course_id, 'staff')

    dist = grades.answer_distributions(request, course)

    d = {}
    d['header'] = ['url_name', 'display name', 'answer id', 'answer', 'count']

    d['data'] = [[url_name, display_name, answer_id, a, answers[a]]
                 for (url_name, display_name, answer_id), answers in dist.items()
                 for a in answers]
    return d


#-----------------------------------------------------------------------------


def compute_course_stats(course):
    '''
    Compute course statistics, including number of problems, videos, html.

    course is a CourseDescriptor from the xmodule system.
    '''

    # walk the course by using get_children() until we come to the leaves; count the
    # number of different leaf types

    counts = defaultdict(int)

    def walk(module):
        children = module.get_children()
        category = module.__class__.__name__ 	# HtmlDescriptor, CapaDescriptor, ...
        counts[category] += 1
        for c in children:
            walk(c)

    walk(course)
    stats = dict(counts)	# number of each kind of module
    return stats
