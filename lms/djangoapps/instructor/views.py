# ======== Instructor views =============================================================================

from collections import defaultdict
import csv
import logging
import os
import urllib

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
import requests

from courseware import grades
from courseware.access import has_access, get_access_group_name
from courseware.courses import get_course_with_access 
from django_comment_client.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from django_comment_client.utils import has_forum_access
from psychometrics import psychoanalyze
from student.models import CourseEnrollment
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
import track.views

log = logging.getLogger("mitx.courseware")

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

    def return_csv(fn, datatable):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(fn)
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(datatable['header'])
        for datarow in datatable['data']:
            encoded_row = [unicode(s).encode('utf-8') for s in datarow]
            writer.writerow(encoded_row)
        return response

    def get_staff_group(course):
        staffgrp = get_access_group_name(course, 'staff')
        try:
            group = Group.objects.get(name=staffgrp)
        except Group.DoesNotExist:
            group = Group(name=staffgrp)		# create the group
            group.save()
        return group

    # process actions from form POST
    action = request.POST.get('action', '')

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

    if action == 'Dump list of enrolled students':
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=False)
        datatable['title'] = 'List of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'list-students', {}, page='idashboard')

    elif 'Dump Grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True)
        datatable['title'] = 'Summary Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'dump-grades', {}, page='idashboard')

    elif 'Dump all RAW grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True,
                                                   get_raw_scores=True)
        datatable['title'] = 'Raw Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, 'dump-grades-raw', {}, page='idashboard')

    elif 'Download CSV of all student grades' in action:
        track.views.server_track(request, 'dump-grades-csv', {}, page='idashboard')
        return return_csv('grades_{0}.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id))

    elif 'Download CSV of all RAW grades' in action:
        track.views.server_track(request, 'dump-grades-csv-raw', {}, page='idashboard')
        return return_csv('grades_{0}_raw.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id, get_raw_scores=True))

    elif 'Download CSV of answer distributions' in action:
        track.views.server_track(request, 'dump-answer-dist-csv', {}, page='idashboard')
        return return_csv('answer_dist_{0}.csv'.format(course_id), get_answers_distribution(request, course_id))

    #----------------------------------------
    # Admin

    elif 'List course staff' in action:
        group = get_staff_group(course)
        msg += 'Staff group = {0}'.format(group.name)
        log.debug('staffgrp={0}'.format(group.name))
        uset = group.user_set.all()
        datatable = {'header': ['Username', 'Full name']}
        datatable['data'] = [[x.username, x.profile.name] for x in uset]
        datatable['title'] = 'List of Staff in course {0}'.format(course_id)
        track.views.server_track(request, 'list-staff', {}, page='idashboard')

    elif action == 'Add course staff':
        uname = request.POST['staffuser']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
            user = None
        if user is not None:
            group = get_staff_group(course)
            msg += '<font color="green">Added {0} to staff group = {1}</font>'.format(user, group.name)
            log.debug('staffgrp={0}'.format(group.name))
            user.groups.add(group)
            track.views.server_track(request, 'add-staff {0}'.format(user), {}, page='idashboard')

    elif action == 'Remove course staff':
        uname = request.POST['staffuser']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "{0}"</font>'.format(uname)
            user = None
        if user is not None:
            group = get_staff_group(course)
            msg += '<font color="green">Removed {0} from staff group = {1}</font>'.format(user, group.name)
            log.debug('staffgrp={0}'.format(group.name))
            user.groups.remove(group)
            track.views.server_track(request, 'remove-staff {0}'.format(user), {}, page='idashboard')

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
    # psychometrics

    elif action == 'Generate Histogram and IRT Plot':
        problem = request.POST['Problem']
        nmsg, plots = psychoanalyze.generate_plots_for_problem(problem)
        msg += nmsg
        track.views.server_track(request, 'psychometrics {0}'.format(problem), {}, page='idashboard')

    if idash_mode=='Psychometrics':
        problems = psychoanalyze.problems_with_psychometric_data(course_id)

    #----------------------------------------
    # analytics

    analytics_json = None

    if idash_mode == 'Analytics':
        req = requests.get(settings.ANALYTICS_SERVER_URL + "get_daily_activity?sid=2")
        #analytics_html = req.text
        analytics_json = req.json
    
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
               'analytics_json' : analytics_json,
               }

    return render_to_response('courseware/instructor_dashboard.html', context)

def _list_course_forum_members(course_id, rolename, datatable):
    ''' 
    Fills in datatable with forum membership information, for a given role,
    so that it will be displayed on instructor dashboard.
    
      course_ID = course's ID string
      rolename = one of "Administrator", "Moderator", "Community TA"
    
    Returns message status string to append to displayed message, if role is unknown.
    '''
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
    

def get_student_grade_summary_data(request, course, course_id, get_grades=True, get_raw_scores=False):
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
    if get_grades:
        # just to construct the header
        gradeset = grades.grade(enrolled_students[0], request, course, keep_raw_scores=get_raw_scores)
        # log.debug('student {0} gradeset {1}'.format(enrolled_students[0], gradeset))
        if get_raw_scores:
            header += [score.section for score in gradeset['raw_scores']]
        else:
            header += [x['label'] for x in gradeset['section_breakdown']]

    datatable = {'header': header}
    data = []

    for student in enrolled_students:
        datarow = [ student.id, student.username, student.profile.name, student.email ]
        try:
            datarow.append(student.externalauthmap.external_email)
        except:	# ExternalAuthMap.DoesNotExist
            datarow.append('')

        if get_grades:
            gradeset = grades.grade(student, request, course, keep_raw_scores=get_raw_scores)
            # log.debug('student={0}, gradeset={1}'.format(student,gradeset))
            if get_raw_scores:
                datarow += [score.earned for score in gradeset['raw_scores']]
            else:
                datarow += [x['percent'] for x in gradeset['section_breakdown']]

        data.append(datarow)
    datatable['data'] = data
    return datatable


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
                     'grade_summary': grades.grade(student, request, course),
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

    if 'new_students' in request.POST:
        new_students = request.POST['new_students'].split('\n')
    else:
        new_students = []
    new_students = [s.strip() for s in new_students]

    added_students = []
    rejected_students = []

    for student in new_students:
        try:
            nce = CourseEnrollment(user=User.objects.get(email=student), course_id=course_id)
            nce.save()
            added_students.append(student)
        except:
            rejected_students.append(student)

    return render_to_response("enroll_students.html", {'course': course_id,
                                                       'existing_students': existing_students,
                                                       'added_students': added_students,
                                                       'rejected_students': rejected_students,
                                                       'debug': new_students})


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
