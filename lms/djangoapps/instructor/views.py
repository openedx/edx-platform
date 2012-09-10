# ======== Instructor views =============================================================================

import csv
import itertools
import json
import logging
import os
import urllib

import track.views

from functools import partial
from collections import defaultdict

from django.conf import settings
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
#from django.views.decorators.csrf import ensure_csrf_cookie
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control

from courseware import grades
from courseware.access import has_access, get_access_group_name
from courseware.courses import (get_course_with_access, get_courses_by_university)
from psychometrics import psychoanalyze
from student.models import UserProfile

from student.models import UserTestGroup, CourseEnrollment
from util.cache import cache, cache_if_anonymous
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location

log = logging.getLogger("mitx.courseware")

template_imports = {'urllib': urllib}


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard(request, course_id):
    """Display the instructor dashboard for a course."""
    course = get_course_with_access(request.user, course_id, 'staff')

    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists

    msg = ''
    #msg += ('POST=%s' % dict(request.POST)).replace('<','&lt;')

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
        response['Content-Disposition'] = 'attachment; filename=%s' % fn
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(datatable['header'])
        for datarow in datatable['data']:
            writer.writerow(datarow)
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
            log.debug('git pull %s' % (data_dir))
            gdir = settings.DATA_DIR / data_dir
            if not os.path.exists(gdir):
                msg += "====> ERROR in gitreload - no such directory %s" % gdir
            else:
                cmd = "cd %s; git reset --hard HEAD; git clean -f -d; git pull origin; chmod g+w course.xml" % gdir
                msg += "git pull on %s:<p>" % data_dir
                msg += "<pre>%s</pre></p>" % escape(os.popen(cmd).read())
                track.views.server_track(request, 'git pull %s' % data_dir, {}, page='idashboard')

        if 'Reload course' in action:
            log.debug('reloading %s (%s)' % (course_id, course))
            try:
                data_dir = course.metadata['data_dir']
                modulestore().try_load_course(data_dir)
                msg += "<br/><p>Course reloaded from %s</p>" % data_dir
                track.views.server_track(request, 'reload %s' % data_dir, {}, page='idashboard')
                course_errors = modulestore().get_item_errors(course.location)
                msg += '<ul>'
                for cmsg, cerr in course_errors:
                    msg += "<li>%s: <pre>%s</pre>" % (cmsg,escape(cerr))
                msg += '</ul>'
            except Exception as err:
                msg += '<br/><p>Error: %s</p>' % escape(err)

    if action == 'Dump list of enrolled students':
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=False)
        datatable['title'] = 'List of students enrolled in %s' % course_id
        track.views.server_track(request, 'list-students', {}, page='idashboard')

    elif 'Dump Grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True)
        datatable['title'] = 'Summary Grades of students enrolled in %s' % course_id
        track.views.server_track(request, 'dump-grades', {}, page='idashboard')

    elif 'Dump all RAW grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True,
                                                   get_raw_scores=True)
        datatable['title'] = 'Raw Grades of students enrolled in %s' % course_id
        track.views.server_track(request, 'dump-grades-raw', {}, page='idashboard')

    elif 'Download CSV of all student grades' in action:
        track.views.server_track(request, 'dump-grades-csv', {}, page='idashboard')
        return return_csv('grades_%s.csv' % course_id,
                          get_student_grade_summary_data(request, course, course_id))

    elif 'Download CSV of all RAW grades' in action:
        track.views.server_track(request, 'dump-grades-csv-raw', {}, page='idashboard')
        return return_csv('grades_%s_raw.csv' % course_id,
                          get_student_grade_summary_data(request, course, course_id, get_raw_scores=True))

    elif 'Download CSV of answer distributions' in action:
        track.views.server_track(request, 'dump-answer-dist-csv', {}, page='idashboard')
        return return_csv('answer_dist_%s.csv' % course_id, get_answers_distribution(request, course_id))

    #----------------------------------------
    # Admin

    elif 'List course staff' in action:
        group = get_staff_group(course)
        msg += 'Staff group = %s' % group.name
        log.debug('staffgrp=%s' % group.name)
        uset = group.user_set.all()
        datatable = {'header': ['Username', 'Full name']}
        datatable['data'] = [[x.username, x.profile.name] for x in uset]
        datatable['title'] = 'List of Staff in course %s' % course_id
        track.views.server_track(request, 'list-staff', {}, page='idashboard')

    elif action == 'Add course staff':
        uname = request.POST['staffuser']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "%s"</font>' % uname
            user = None
        if user is not None:
            group = get_staff_group(course)
            msg += '<font color="green">Added %s to staff group = %s</font>' % (user, group.name)
            log.debug('staffgrp=%s' % group.name)
            user.groups.add(group)
            track.views.server_track(request, 'add-staff %s' % user, {}, page='idashboard')

    elif action == 'Remove course staff':
        uname = request.POST['staffuser']
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            msg += '<font color="red">Error: unknown username "%s"</font>' % uname
            user = None
        if user is not None:
            group = get_staff_group(course)
            msg += '<font color="green">Removed %s from staff group = %s</font>' % (user, group.name)
            log.debug('staffgrp=%s' % group.name)
            user.groups.remove(group)
            track.views.server_track(request, 'remove-staff %s' % user, {}, page='idashboard')

    #----------------------------------------
    # psychometrics

    elif action == 'Generate Histogram and IRT Plot':
        problem = request.POST['Problem']
        nmsg, plots = psychoanalyze.generate_plots_for_problem(problem)
        msg += nmsg
        track.views.server_track(request, 'psychometrics %s' % problem, {}, page='idashboard')

    if idash_mode=='Psychometrics':
        problems = psychoanalyze.problems_with_psychometric_data(course_id)

    #----------------------------------------
    # context for rendering
    context = {'course': course,
               'staff_access': True,
               'admin_access': request.user.is_staff,
               'instructor_access': instructor_access,
               'datatable': datatable,
               'msg': msg,
               'modeflag': {idash_mode: 'selectedmode'},
               'problems': problems,		# psychometrics
               'plots': plots,			# psychometrics
               'course_errors': modulestore().get_item_errors(course.location),
               'djangopid' : os.getpid(),
               }

    return render_to_response('courseware/instructor_dashboard.html', context)


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
    enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).order_by('username')

    header = ['ID', 'Username', 'Full Name', 'edX email', 'External email']
    if get_grades:
        # just to construct the header
        gradeset = grades.grade(enrolled_students[0], request, course, keep_raw_scores=get_raw_scores)
        # log.debug('student %s gradeset %s' % (enrolled_students[0], gradeset))
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
            # log.debug('student=%s, gradeset=%s' % (student,gradeset))
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

    enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).order_by('username')

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
