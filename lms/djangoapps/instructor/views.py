"""
Instructor Views
"""
from collections import defaultdict
import csv
import json
import logging
from markupsafe import escape
import os
import re
import requests
from requests.status_codes import codes
from collections import OrderedDict

from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.utils import timezone

import xmodule.graders as xmgraders
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware import grades
from courseware.access import (has_access, get_access_group_name,
                               course_beta_test_group_name)
from courseware.courses import get_course_with_access
from courseware.models import StudentModule
from django_comment_common.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)
from django_comment_client.utils import has_forum_access
from instructor.offline_gradecalc import student_grades, offline_grades_available
from instructor_task.api import (get_running_instructor_tasks,
                                 get_instructor_task_history,
                                 submit_rescore_problem_for_all_students,
                                 submit_rescore_problem_for_student,
                                 submit_reset_problem_attempts_for_all_students)
from instructor_task.views import get_task_completion_info
from mitxmako.shortcuts import render_to_response
from psychometrics import psychoanalyze
from student.models import CourseEnrollment, CourseEnrollmentAllowed
import track.views
from mitxmako.shortcuts import render_to_string


log = logging.getLogger(__name__)

# internal commands for managing forum roles:
FORUM_ROLE_ADD = 'add'
FORUM_ROLE_REMOVE = 'remove'


def split_by_comma_and_whitespace(s):
    """
    Return string s, split by , or whitespace
    """
    return re.split(r'[\s,]', s)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard(request, course_id):
    """Display the instructor dashboard for a course."""
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists

    forum_admin_access = has_forum_access(request.user, course_id, FORUM_ROLE_ADMINISTRATOR)

    msg = ''
    problems = []
    plots = []
    datatable = {}

    # the instructor dashboard page is modal: grades, psychometrics, admin
    # keep that state in request.session (defaults to grades mode)
    idash_mode = request.POST.get('idash_mode', '')
    if idash_mode:
        request.session['idash_mode'] = idash_mode
    else:
        idash_mode = request.session.get('idash_mode', 'Grades')

    # assemble some course statistics for output to instructor
    def get_course_stats_table():
        datatable = {'header': ['Statistic', 'Value'],
                     'title': 'Course Statistics At A Glance',
                     }
        data = [['# Enrolled', CourseEnrollment.objects.filter(course_id=course_id).count()]]
        data += [['Date', timezone.now().isoformat()]]
        data += compute_course_stats(course).items()
        if request.user.is_staff:
            for field in course.fields:
                if getattr(field.scope, 'user', False):
                    continue

                data.append([field.name, json.dumps(field.read_json(course))])
            for namespace in course.namespaces:
                for field in getattr(course, namespace).fields:
                    if getattr(field.scope, 'user', False):
                        continue

                    data.append(["{}.{}".format(namespace, field.name), json.dumps(field.read_json(course))])
        datatable['data'] = data
        return datatable

    def return_csv(fn, datatable, fp=None):
        """Outputs a CSV file from the contents of a datatable."""
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
        """Get or create the staff access group"""
        return get_group(course, 'staff')

    def get_instructor_group(course):
        """Get or create the instructor access group"""
        return get_group(course, 'instructor')

    def get_group(course, groupname):
        """Get or create an access group"""
        grpname = get_access_group_name(course, groupname)
        try:
            group = Group.objects.get(name=grpname)
        except Group.DoesNotExist:
            group = Group(name=grpname)     # create the group
            group.save()
        return group

    def get_beta_group(course):
        """
        Get the group for beta testers of course.
        """
        # Not using get_group because there is no access control action called
        # 'beta', so adding it to get_access_group_name doesn't really make
        # sense.
        name = course_beta_test_group_name(course.location)
        (group, _) = Group.objects.get_or_create(name=name)
        return group

    def get_module_url(urlname):
        """
        Construct full URL for a module from its urlname.

        Form is either urlname or modulename/urlname.  If no modulename
        is provided, "problem" is assumed.
        """
        # tolerate an XML suffix in the urlname
        if urlname[-4:] == ".xml":
            urlname = urlname[:-4]

        # implement default
        if '/' not in urlname:
            urlname = "problem/" + urlname

        # complete the url using information about the current course:
        (org, course_name, _) = course_id.split("/")
        return "i4x://" + org + "/" + course_name + "/" + urlname

    def get_student_from_identifier(unique_student_identifier):
        """Gets a student object using either an email address or username"""
        msg = ""
        try:
            if "@" in unique_student_identifier:
                student = User.objects.get(email=unique_student_identifier)
            else:
                student = User.objects.get(username=unique_student_identifier)
            msg += "Found a single student.  "
        except User.DoesNotExist:
            student = None
            msg += "<font color='red'>Couldn't find student with that email or username.  </font>"
        return msg, student

    # process actions from form POST
    action = request.POST.get('action', '')
    use_offline = request.POST.get('use_offline_grades', False)

    if settings.MITX_FEATURES['ENABLE_MANUAL_GIT_RELOAD']:
        if 'GIT pull' in action:
            data_dir = getattr(course, 'data_dir')
            log.debug('git pull {0}'.format(data_dir))
            gdir = settings.DATA_DIR / data_dir
            if not os.path.exists(gdir):
                msg += "====> ERROR in gitreload - no such directory {0}".format(gdir)
            else:
                cmd = "cd {0}; git reset --hard HEAD; git clean -f -d; git pull origin; chmod g+w course.xml".format(gdir)
                msg += "git pull on {0}:<p>".format(data_dir)
                msg += "<pre>{0}</pre></p>".format(escape(os.popen(cmd).read()))
                track.views.server_track(request, "git-pull", {"directory": data_dir}, page="idashboard")

        if 'Reload course' in action:
            log.debug('reloading {0} ({1})'.format(course_id, course))
            try:
                data_dir = getattr(course, 'data_dir')
                modulestore().try_load_course(data_dir)
                msg += "<br/><p>Course reloaded from {0}</p>".format(data_dir)
                track.views.server_track(request, "reload", {"directory": data_dir}, page="idashboard")
                course_errors = modulestore().get_item_errors(course.location)
                msg += '<ul>'
                for cmsg, cerr in course_errors:
                    msg += "<li>{0}: <pre>{1}</pre>".format(cmsg, escape(cerr))
                msg += '</ul>'
            except Exception as err:
                msg += '<br/><p>Error: {0}</p>'.format(escape(err))

    if action == 'Dump list of enrolled students' or action == 'List enrolled students':
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=False, use_offline=use_offline)
        datatable['title'] = 'List of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, "list-students", {}, page="idashboard")

    elif 'Dump Grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True, use_offline=use_offline)
        datatable['title'] = 'Summary Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, "dump-grades", {}, page="idashboard")

    elif 'Dump all RAW grades' in action:
        log.debug(action)
        datatable = get_student_grade_summary_data(request, course, course_id, get_grades=True,
                                                   get_raw_scores=True, use_offline=use_offline)
        datatable['title'] = 'Raw Grades of students enrolled in {0}'.format(course_id)
        track.views.server_track(request, "dump-grades-raw", {}, page="idashboard")

    elif 'Download CSV of all student grades' in action:
        track.views.server_track(request, "dump-grades-csv", {}, page="idashboard")
        return return_csv('grades_{0}.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id, use_offline=use_offline))

    elif 'Download CSV of all RAW grades' in action:
        track.views.server_track(request, "dump-grades-csv-raw", {}, page="idashboard")
        return return_csv('grades_{0}_raw.csv'.format(course_id),
                          get_student_grade_summary_data(request, course, course_id, get_raw_scores=True, use_offline=use_offline))

    elif 'Download CSV of answer distributions' in action:
        track.views.server_track(request, "dump-answer-dist-csv", {}, page="idashboard")
        return return_csv('answer_dist_{0}.csv'.format(course_id), get_answers_distribution(request, course_id))

    elif 'Dump description of graded assignments configuration' in action:
        # what is "graded assignments configuration"?
        track.views.server_track(request, "dump-graded-assignments-config", {}, page="idashboard")
        msg += dump_grading_context(course)

    elif "Rescore ALL students' problem submissions" in action:
        problem_urlname = request.POST.get('problem_for_all_students', '')
        problem_url = get_module_url(problem_urlname)
        try:
            instructor_task = submit_rescore_problem_for_all_students(request, course_id, problem_url)
            if instructor_task is None:
                msg += '<font color="red">Failed to create a background task for rescoring "{0}".</font>'.format(problem_url)
            else:
                track.views.server_track(request, "rescore-all-submissions", {"problem": problem_url, "course": course_id}, page="idashboard")
        except ItemNotFoundError as e:
            msg += '<font color="red">Failed to create a background task for rescoring "{0}": problem not found.</font>'.format(problem_url)
        except Exception as e:
            log.error("Encountered exception from rescore: {0}".format(e))
            msg += '<font color="red">Failed to create a background task for rescoring "{0}": {1}.</font>'.format(problem_url, e.message)

    elif "Reset ALL students' attempts" in action:
        problem_urlname = request.POST.get('problem_for_all_students', '')
        problem_url = get_module_url(problem_urlname)
        try:
            instructor_task = submit_reset_problem_attempts_for_all_students(request, course_id, problem_url)
            if instructor_task is None:
                msg += '<font color="red">Failed to create a background task for resetting "{0}".</font>'.format(problem_url)
            else:
                track.views.server_track(request, "reset-all-attempts", {"problem": problem_url, "course": course_id}, page="idashboard")
        except ItemNotFoundError as e:
            log.error('Failure to reset: unknown problem "{0}"'.format(e))
            msg += '<font color="red">Failed to create a background task for resetting "{0}": problem not found.</font>'.format(problem_url)
        except Exception as e:
            log.error("Encountered exception from reset: {0}".format(e))
            msg += '<font color="red">Failed to create a background task for resetting "{0}": {1}.</font>'.format(problem_url, e.message)

    elif "Show Background Task History for Student" in action:
        # put this before the non-student case, since the use of "in" will cause this to be missed
        unique_student_identifier = request.POST.get('unique_student_identifier', '')
        message, student = get_student_from_identifier(unique_student_identifier)
        if student is None:
            msg += message
        else:
            problem_urlname = request.POST.get('problem_for_student', '')
            problem_url = get_module_url(problem_urlname)
            message, datatable = get_background_task_table(course_id, problem_url, student)
            msg += message

    elif "Show Background Task History" in action:
        problem_urlname = request.POST.get('problem_for_all_students', '')
        problem_url = get_module_url(problem_urlname)
        message, datatable = get_background_task_table(course_id, problem_url)
        msg += message

    elif ("Reset student's attempts" in action or
          "Delete student state for module" in action or
          "Rescore student's problem submission" in action):
        # get the form data
        unique_student_identifier = request.POST.get('unique_student_identifier', '')
        problem_urlname = request.POST.get('problem_for_student', '')
        module_state_key = get_module_url(problem_urlname)
        # try to uniquely id student by email address or username
        message, student = get_student_from_identifier(unique_student_identifier)
        msg += message
        student_module = None
        if student is not None:
            # find the module in question
            try:
                student_module = StudentModule.objects.get(
                    student_id=student.id,
                    course_id=course_id,
                    module_state_key=module_state_key
                )
                msg += "Found module.  "
            except StudentModule.DoesNotExist as err:
                msg += "<font color='red'>Couldn't find module with that urlname.  </font>"
                msg += "<font color='red'>Error: {0}  </font>".format(err.message)
                log.exception(msg)

        if student_module is not None:
            if "Delete student state for module" in action:
                # delete the state
                try:
                    student_module.delete()
                    msg += "<font color='red'>Deleted student module state for %s!</font>" % module_state_key
                    event = {"problem": problem_url, "student": unique_student_identifier, "course": course_id}
                    track.views.server_track(request, "delete-student-module-state", event, page="idashboard")
                except Exception as err:
                    msg += "Failed to delete module state for {0}/{1} ".format(unique_student_identifier, problem_urlname)
                    msg += "<font color='red'>Error: {0}  </font>".format(err.message)
                    log.exception(msg)
            elif "Reset student's attempts" in action:
                # modify the problem's state
                try:
                    # load the state json
                    problem_state = json.loads(student_module.state)
                    old_number_of_attempts = problem_state["attempts"]
                    problem_state["attempts"] = 0
                    # save
                    student_module.state = json.dumps(problem_state)
                    student_module.save()
                    event = {
                        "old_attempts": old_number_of_attempts,
                        "student": unicode(student),
                        "problem": student_module.module_state_key,
                        "instructor": unicode(request.user),
                        "course": course_id
                    }
                    track.views.server_track(request, "reset-student-attempts", event, page="idashboard")
                    msg += "<font color='green'>Module state successfully reset!</font>"
                except Exception as err:
                    msg += "<font color='red'>Couldn't reset module state.  </font>"
                    msg += "<font color='red'>Error: {0}  </font>".format(err.message)
                    log.exception(msg)
            else:
                # "Rescore student's problem submission" case
                try:
                    instructor_task = submit_rescore_problem_for_student(request, course_id, module_state_key, student)
                    if instructor_task is None:
                        msg += '<font color="red">Failed to create a background task for rescoring "{0}" for student {1}.</font>'.format(module_state_key, unique_student_identifier)
                    else:
                        track.views.server_track(request, "rescore-student-submission", {"problem": module_state_key, "student": unique_student_identifier, "course": course_id}, page="idashboard")
                except Exception as err:
                    msg += '<font color="red">Failed to create a background task for rescoring "{0}": {1}.</font>'.format(module_state_key, err.message)
                    log.exception(msg)

    elif "Get link to student's progress page" in action:
        unique_student_identifier = request.POST.get('unique_student_identifier', '')
        # try to uniquely id student by email address or username
        message, student = get_student_from_identifier(unique_student_identifier)
        msg += message
        if student is not None:
            progress_url = reverse('student_progress', kwargs={'course_id': course_id, 'student_id': student.id})
            track.views.server_track(request, "get-student-progress-page", {"student": unicode(student), "instructor": unicode(request.user), "course": course_id}, page="idashboard")
            msg += "<a href='{0}' target='_blank'> Progress page for username: {1} with email address: {2}</a>.".format(progress_url, student.username, student.email)

    #----------------------------------------
    # export grades to remote gradebook

    elif action == 'List assignments available in remote gradebook':
        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-assignments')
        msg += msg2

    elif action == 'List assignments available for this course':
        log.debug(action)
        allgrades = get_student_grade_summary_data(request, course, course_id, get_grades=True, use_offline=use_offline)

        assignments = [[x] for x in allgrades['assignments']]
        datatable = {'header': ['Assignment Name']}
        datatable['data'] = assignments
        datatable['title'] = action

        msg += 'assignments=<pre>%s</pre>' % assignments

    elif action == 'List enrolled students matching remote gradebook':
        stud_data = get_student_grade_summary_data(request, course, course_id, get_grades=False, use_offline=use_offline)
        msg2, rg_stud_data = _do_remote_gradebook(request.user, course, 'get-membership')
        datatable = {'header': ['Student  email', 'Match?']}
        rg_students = [x['email'] for x in rg_stud_data['retdata']]

        def domatch(x):
            return 'yes' if x.email in rg_students else 'No'
        datatable['data'] = [[x.email, domatch(x)] for x in stud_data['students']]
        datatable['title'] = action

    elif action in ['Display grades for assignment', 'Export grades for assignment to remote gradebook',
                    'Export CSV file of grades for assignment']:

        log.debug(action)
        datatable = {}
        aname = request.POST.get('assignment_name', '')
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
                    msg2, _ = _do_remote_gradebook(request.user, course, 'post-grades', files=files)
                    msg += msg2

    #----------------------------------------
    # Admin

    elif 'List course staff' in action:
        group = get_staff_group(course)
        msg += 'Staff group = {0}'.format(group.name)
        datatable = _group_members_table(group, "List of Staff", course_id)
        track.views.server_track(request, "list-staff", {}, page="idashboard")

    elif 'List course instructors' in action and request.user.is_staff:
        group = get_instructor_group(course)
        msg += 'Instructor group = {0}'.format(group.name)
        log.debug('instructor grp={0}'.format(group.name))
        uset = group.user_set.all()
        datatable = {'header': ['Username', 'Full name']}
        datatable['data'] = [[x.username, x.profile.name] for x in uset]
        datatable['title'] = 'List of Instructors in course {0}'.format(course_id)
        track.views.server_track(request, "list-instructors", {}, page="idashboard")

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
            track.views.server_track(request, "add-instructor", {"instructor": unicode(user)}, page="idashboard")

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
            track.views.server_track(request, "remove-instructor", {"instructor": unicode(user)}, page="idashboard")

    #----------------------------------------
    # DataDump

    elif 'Download CSV of all student profile data' in action:
        enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).order_by('username').select_related("profile")
        profkeys = ['name', 'language', 'location', 'year_of_birth', 'gender', 'level_of_education',
                    'mailing_address', 'goals']
        datatable = {'header': ['username', 'email'] + profkeys}

        def getdat(u):
            p = u.profile
            return [u.username, u.email] + [getattr(p, x, '') for x in profkeys]

        datatable['data'] = [getdat(u) for u in enrolled_students]
        datatable['title'] = 'Student profile data for course %s' % course_id
        return return_csv('profiledata_%s.csv' % course_id, datatable)

    elif 'Download CSV of all responses to problem' in action:
        problem_to_dump = request.POST.get('problem_to_dump', '')

        if problem_to_dump[-4:] == ".xml":
            problem_to_dump = problem_to_dump[:-4]
        try:
            (org, course_name, _) = course_id.split("/")
            module_state_key = "i4x://" + org + "/" + course_name + "/problem/" + problem_to_dump
            smdat = StudentModule.objects.filter(course_id=course_id,
                                                 module_state_key=module_state_key)
            smdat = smdat.order_by('student')
            msg += "Found %d records to dump " % len(smdat)
        except Exception as err:
            msg += "<font color='red'>Couldn't find module with that urlname.  </font>"
            msg += "<pre>%s</pre>" % escape(err)
            smdat = []

        if smdat:
            datatable = {'header': ['username', 'state']}
            datatable['data'] = [[x.student.username, x.state] for x in smdat]
            datatable['title'] = 'Student state for problem %s' % problem_to_dump
            return return_csv('student_state_from_%s.csv' % problem_to_dump, datatable)

    #----------------------------------------
    # Group management

    elif 'List beta testers' in action:
        group = get_beta_group(course)
        msg += 'Beta test group = {0}'.format(group.name)
        datatable = _group_members_table(group, "List of beta_testers", course_id)
        track.views.server_track(request, "list-beta-testers", {}, page="idashboard")

    elif action == 'Add beta testers':
        users = request.POST['betausers']
        log.debug("users: {0!r}".format(users))
        group = get_beta_group(course)
        for username_or_email in split_by_comma_and_whitespace(users):
            msg += "<p>{0}</p>".format(
                add_user_to_group(request, username_or_email, group, 'beta testers', 'beta-tester'))

    elif action == 'Remove beta testers':
        users = request.POST['betausers']
        group = get_beta_group(course)
        for username_or_email in split_by_comma_and_whitespace(users):
            msg += "<p>{0}</p>".format(
                remove_user_from_group(request, username_or_email, group, 'beta testers', 'beta-tester'))

    #----------------------------------------
    # forum administration

    elif action == 'List course forum admins':
        rolename = FORUM_ROLE_ADMINISTRATOR
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, "list-forum-admins", {"course": course_id}, page="idashboard")

    elif action == 'Remove forum admin':
        uname = request.POST['forumadmin']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_REMOVE)
        track.views.server_track(request, "remove-forum-admin", {"username": uname, "course": course_id}, page="idashboard")

    elif action == 'Add forum admin':
        uname = request.POST['forumadmin']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_ADD)
        track.views.server_track(request, "add-forum-admin", {"username": uname, "course": course_id}, page="idashboard")

    elif action == 'List course forum moderators':
        rolename = FORUM_ROLE_MODERATOR
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, "list-forum-mods", {"course": course_id}, page="idashboard")

    elif action == 'Remove forum moderator':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_MODERATOR, FORUM_ROLE_REMOVE)
        track.views.server_track(request, "remove-forum-mod", {"username": uname, "course": course_id}, page="idashboard")

    elif action == 'Add forum moderator':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_MODERATOR, FORUM_ROLE_ADD)
        track.views.server_track(request, "add-forum-mod", {"username": uname, "course": course_id}, page="idashboard")

    elif action == 'List course forum community TAs':
        rolename = FORUM_ROLE_COMMUNITY_TA
        datatable = {}
        msg += _list_course_forum_members(course_id, rolename, datatable)
        track.views.server_track(request, "list-forum-community-TAs", {"course": course_id}, page="idashboard")

    elif action == 'Remove forum community TA':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_REMOVE)
        track.views.server_track(request, "remove-forum-community-TA", {"username": uname, "course": course_id}, page="idashboard")

    elif action == 'Add forum community TA':
        uname = request.POST['forummoderator']
        msg += _update_forum_role_membership(uname, course, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_ADD)
        track.views.server_track(request, "add-forum-community-TA", {"username": uname, "course": course_id}, page="idashboard")

    #----------------------------------------
    # enrollment

    elif action == 'List students who may enroll but may not have yet signed up':
        ceaset = CourseEnrollmentAllowed.objects.filter(course_id=course_id)
        datatable = {'header': ['StudentEmail']}
        datatable['data'] = [[x.email] for x in ceaset]
        datatable['title'] = action

    elif action == 'Enroll multiple students':

        students = request.POST.get('multiple_students', '')
        auto_enroll = bool(request.POST.get('auto_enroll'))
        email_students = bool(request.POST.get('email_students'))
        ret = _do_enroll_students(course, course_id, students, auto_enroll=auto_enroll, email_students=email_students)
        datatable = ret['datatable']

    elif action == 'Unenroll multiple students':

        students = request.POST.get('multiple_students', '')
        email_students = bool(request.POST.get('email_students'))
        ret = _do_unenroll_students(course_id, students, email_students=email_students)
        datatable = ret['datatable']

    elif action == 'List sections available in remote gradebook':

        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-sections')
        msg += msg2

    elif action in ['List students in section in remote gradebook',
                    'Overload enrollment list using remote gradebook',
                    'Merge enrollment list with remote gradebook']:

        section = request.POST.get('gradebook_section', '')
        msg2, datatable = _do_remote_gradebook(request.user, course, 'get-membership', dict(section=section))
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
        track.views.server_track(request, "psychometrics-histogram-generation", {"problem": unicode(problem)}, page="idashboard")

    if idash_mode == 'Psychometrics':
        problems = psychoanalyze.problems_with_psychometric_data(course_id)

    #----------------------------------------
    # analytics
    def get_analytics_result(analytics_name):
        """Return data for an Analytic piece, or None if it doesn't exist. It
        logs and swallows errors.
        """
        url = settings.ANALYTICS_SERVER_URL + \
            "get?aname={}&course_id={}&apikey={}".format(analytics_name,
                                                         course_id,
                                                         settings.ANALYTICS_API_KEY)
        try:
            res = requests.get(url)
        except Exception:
            log.exception("Error trying to access analytics at %s", url)
            return None

        if res.status_code == codes.OK:
            # WARNING: do not use req.json because the preloaded json doesn't
            # preserve the order of the original record (hence OrderedDict).
            return json.loads(res.content, object_pairs_hook=OrderedDict)
        else:
            log.error("Error fetching %s, code: %s, msg: %s",
                      url, res.status_code, res.content)
        return None

    analytics_results = {}

    if idash_mode == 'Analytics':
        DASHBOARD_ANALYTICS = [
            # "StudentsAttemptedProblems",  # num students who tried given problem
            "StudentsDailyActivity",  # active students by day
            "StudentsDropoffPerDay",  # active students dropoff by day
            # "OverallGradeDistribution",  # overall point distribution for course
            "StudentsActive",  # num students active in time period (default = 1wk)
            "StudentsEnrolled",  # num students enrolled
            # "StudentsPerProblemCorrect",  # foreach problem, num students correct
            "ProblemGradeDistribution",  # foreach problem, grade distribution
        ]
        for analytic_name in DASHBOARD_ANALYTICS:
            analytics_results[analytic_name] = get_analytics_result(analytic_name)

    #----------------------------------------
    # offline grades?

    if use_offline:
        msg += "<br/><font color='orange'>Grades from %s</font>" % offline_grades_available(course_id)

    # generate list of pending background tasks
    if settings.MITX_FEATURES.get('ENABLE_INSTRUCTOR_BACKGROUND_TASKS'):
        instructor_tasks = get_running_instructor_tasks(course_id)
    else:
        instructor_tasks = None

    # display course stats only if there is no other table to display:
    course_stats = None
    if not datatable:
        course_stats = get_course_stats_table()
    #----------------------------------------
    # context for rendering

    context = {'course': course,
               'staff_access': True,
               'admin_access': request.user.is_staff,
               'instructor_access': instructor_access,
               'forum_admin_access': forum_admin_access,
               'datatable': datatable,
               'course_stats': course_stats,
               'msg': msg,
               'modeflag': {idash_mode: 'selectedmode'},
               'problems': problems,		# psychometrics
               'plots': plots,			# psychometrics
               'course_errors': modulestore().get_item_errors(course.location),
               'instructor_tasks': instructor_tasks,
               'djangopid': os.getpid(),
               'mitx_version': getattr(settings, 'MITX_VERSION_STRING', ''),
               'offline_grade_log': offline_grades_available(course_id),
               'cohorts_ajax_url': reverse('cohorts', kwargs={'course_id': course_id}),

               'analytics_results': analytics_results,
               }

    return render_to_response('courseware/instructor_dashboard.html', context)


def _do_remote_gradebook(user, course, action, args=None, files=None):
    '''
    Perform remote gradebook action.  Returns msg, datatable.
    '''
    rg = course.remote_gradebook
    if not rg:
        msg = "No remote gradebook defined in course metadata"
        return msg, {}

    rgurl = settings.MITX_FEATURES.get('REMOTE_GRADEBOOK_URL', '')
    if not rgurl:
        msg = "No remote gradebook url defined in settings.MITX_FEATURES"
        return msg, {}

    rgname = rg.get('name', '')
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

    msg = '<pre>%s</pre>' % retdict['msg'].replace('\n', '<br/>')
    retdata = retdict['data']  	# a list of dicts

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
    datatable['data'] = []
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
            msg = '<font color="red">Error: user "{0}" does not have rolename "{1}", cannot remove</font>'.format(uname, rolename)
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


def _add_or_remove_user_group(request, username_or_email, group, group_title, event_name, do_add):
    """
    Implementation for both add and remove functions, to get rid of shared code.  do_add is bool that determines which
    to do.
    """
    user = None
    try:
        if '@' in username_or_email:
            user = User.objects.get(email=username_or_email)
        else:
            user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        msg = '<font color="red">Error: unknown username or email "{0}"</font>'.format(username_or_email)
        user = None

    if user is not None:
        action = "Added" if do_add else "Removed"
        prep = "to" if do_add else "from"
        msg = '<font color="green">{action} {0} {prep} {1} group = {2}</font>'.format(user, group_title, group.name,
                                                                                      action=action, prep=prep)
        if do_add:
            user.groups.add(group)
        else:
            user.groups.remove(group)
        event = "add" if do_add else "remove"
        track.views.server_track(request, "add-or-remove-user-group", {"event_name": event_name, "user": unicode(user), "event": event}, page="idashboard")

    return msg


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
    return _add_or_remove_user_group(request, username_or_email, group, group_title, event_name, True)


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
    return _add_or_remove_user_group(request, username_or_email, group, group_title, event_name, False)


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
        datarow = [student.id, student.username, student.profile.name, student.email]
        try:
            datarow.append(student.externalauthmap.external_email)
        except:  # ExternalAuthMap.DoesNotExist
            datarow.append('')

        if get_grades:
            gradeset = student_grades(student, request, course, keep_raw_scores=get_raw_scores, use_offline=use_offline)
            log.debug('student={0}, gradeset={1}'.format(student, gradeset))
            if get_raw_scores:
                # TODO (ichuang) encode Score as dict instead of as list, so score[0] -> score['earned']
                sgrades = [(getattr(score, 'earned', '') or score[0]) for score in gradeset['raw_scores']]
            else:
                sgrades = [x['percent'] for x in gradeset['section_breakdown']]
            datarow += sgrades
            student.grades = sgrades  	# store in student object

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
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

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

    return render_to_response('courseware/gradebook.html', {
        'students': student_info,
        'course': course,
        'course_id': course_id,
        # Checked above
        'staff_access': True,
        'ordered_grades': sorted(course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True),
    })


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

def _do_enroll_students(course, course_id, students, overload=False, auto_enroll=False, email_students=False):
    """
    Do the actual work of enrolling multiple students, presented as a string
    of emails separated by commas or returns
    `course` is course object
    `course_id` id of course (a `str`)
    `students` string of student emails separated by commas or returns (a `str`)
    `overload` un-enrolls all existing students (a `boolean`)
    `auto_enroll` is user input preference (a `boolean`)
    `email_students` is user input preference (a `boolean`)
    """

    new_students, new_students_lc = get_and_clean_student_list(students)
    status = dict([x, 'unprocessed'] for x in new_students)

    if overload:  	# delete all but staff
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

    if email_students:
        registration_url = 'https://' + settings.SITE_NAME + reverse('student.views.register_user')
        #Composition of email
        d = {'site_name': settings.SITE_NAME,
             'registration_url': registration_url,
             'course_id': course_id,
             'auto_enroll': auto_enroll,
             'course_url': 'https://' + settings.SITE_NAME + '/courses/' + course_id,
             }

    for student in new_students:
        try:
            user = User.objects.get(email=student)
        except User.DoesNotExist:

            #Student not signed up yet, put in pending enrollment allowed table
            cea = CourseEnrollmentAllowed.objects.filter(email=student, course_id=course_id)

            #If enrollmentallowed already exists, update auto_enroll flag to however it was set in UI
            #Will be 0 or 1 records as there is a unique key on email + course_id
            if cea:
                cea[0].auto_enroll = auto_enroll
                cea[0].save()
                status[student] = 'user does not exist, enrollment already allowed, pending with auto enrollment ' \
                    + ('on' if auto_enroll else 'off')
                continue

            #EnrollmentAllowed doesn't exist so create it
            cea = CourseEnrollmentAllowed(email=student, course_id=course_id, auto_enroll=auto_enroll)
            cea.save()

            status[student] = 'user does not exist, enrollment allowed, pending with auto enrollment ' \
                + ('on' if auto_enroll else 'off')

            if email_students:
                #User is allowed to enroll but has not signed up yet
                d['email_address'] = student
                d['message'] = 'allowed_enroll'
                send_mail_ret = send_mail_to_student(student, d)
                status[student] += (', email sent' if send_mail_ret else '')
            continue

        #Student has already registered
        if CourseEnrollment.objects.filter(user=user, course_id=course_id):
            status[student] = 'already enrolled'
            continue

        try:
            #Not enrolled yet
            ce = CourseEnrollment(user=user, course_id=course_id)
            ce.save()
            status[student] = 'added'

            if email_students:
                #User enrolled for first time, populate dict with user specific info
                d['email_address'] = student
                d['first_name'] = user.first_name
                d['last_name'] = user.last_name
                d['message'] = 'enrolled_enroll'
                send_mail_ret = send_mail_to_student(student, d)
                status[student] += (', email sent' if send_mail_ret else '')

        except:
            status[student] = 'rejected'

    datatable = {'header': ['StudentEmail', 'action']}
    datatable['data'] = [[x, status[x]] for x in sorted(status)]
    datatable['title'] = 'Enrollment of students'

    def sf(stat):
        return [x for x in status if status[x] == stat]

    data = dict(added=sf('added'), rejected=sf('rejected') + sf('exists'),
                deleted=sf('deleted'), datatable=datatable)

    return data


#Unenrollment
def _do_unenroll_students(course_id, students, email_students=False):
    """
    Do the actual work of un-enrolling multiple students, presented as a string
    of emails separated by commas or returns
    `course_id` is id of course (a `str`)
    `students` is string of student emails separated by commas or returns (a `str`)
    `email_students` is user input preference (a `boolean`)
    """

    old_students, _ = get_and_clean_student_list(students)
    status = dict([x, 'unprocessed'] for x in old_students)

    if email_students:
        #Composition of email
        d = {'site_name': settings.SITE_NAME,
             'course_id': course_id}

    for student in old_students:

        isok = False
        cea = CourseEnrollmentAllowed.objects.filter(course_id=course_id, email=student)
        #Will be 0 or 1 records as there is a unique key on email + course_id
        if cea:
            cea[0].delete()
            status[student] = "un-enrolled"
            isok = True

        try:
            user = User.objects.get(email=student)
        except User.DoesNotExist:

            if isok and email_students:
                #User was allowed to join but had not signed up yet
                d['email_address'] = student
                d['message'] = 'allowed_unenroll'
                send_mail_ret = send_mail_to_student(student, d)
                status[student] += (', email sent' if send_mail_ret else '')

            continue

        ce = CourseEnrollment.objects.filter(user=user, course_id=course_id)
        #Will be 0 or 1 records as there is a unique key on user + course_id
        if ce:
            try:
                ce[0].delete()
                status[student] = "un-enrolled"
                if email_students:
                    #User was enrolled
                    d['email_address'] = student
                    d['first_name'] = user.first_name
                    d['last_name'] = user.last_name
                    d['message'] = 'enrolled_unenroll'
                    send_mail_ret = send_mail_to_student(student, d)
                    status[student] += (', email sent' if send_mail_ret else '')

            except Exception:
                if not isok:
                    status[student] = "Error!  Failed to un-enroll"

    datatable = {'header': ['StudentEmail', 'action']}
    datatable['data'] = [[x, status[x]] for x in sorted(status)]
    datatable['title'] = 'Un-enrollment of students'

    data = dict(datatable=datatable)
    return data


def send_mail_to_student(student, param_dict):
    """
    Construct the email using templates and then send it.
    `student` is the student's email address (a `str`),

    `param_dict` is a `dict` with keys [
    `site_name`: name given to edX instance (a `str`)
    `registration_url`: url for registration (a `str`)
    `course_id`: id of course (a `str`)
    `auto_enroll`: user input option (a `str`)
    `course_url`: url of course (a `str`)
    `email_address`: email of student (a `str`)
    `first_name`: student first name (a `str`)
    `last_name`: student last name (a `str`)
    `message`: type of email to send and template to use (a `str`)
                                        ]
    Returns a boolean indicating whether the email was sent successfully.
    """

    EMAIL_TEMPLATE_DICT = {'allowed_enroll': ('emails/enroll_email_allowedsubject.txt', 'emails/enroll_email_allowedmessage.txt'),
                           'enrolled_enroll': ('emails/enroll_email_enrolledsubject.txt', 'emails/enroll_email_enrolledmessage.txt'),
                           'allowed_unenroll': ('emails/unenroll_email_subject.txt', 'emails/unenroll_email_allowedmessage.txt'),
                           'enrolled_unenroll': ('emails/unenroll_email_subject.txt', 'emails/unenroll_email_enrolledmessage.txt')}

    subject_template, message_template = EMAIL_TEMPLATE_DICT.get(param_dict['message'], (None, None))
    if subject_template is not None and message_template is not None:
        subject = render_to_string(subject_template, param_dict)
        message = render_to_string(message_template, param_dict)

        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student], fail_silently=False)
        return True
    else:
        return False


def get_and_clean_student_list(students):
    """
    Separate out individual student email from the comma, or space separated string.
    `students` is string of student emails separated by commas or returns (a `str`)
    Returns:
    students: list of cleaned student emails
    students_lc: list of lower case cleaned student emails
    """

    students = split_by_comma_and_whitespace(students)
    students = [str(s.strip()) for s in students]
    students = [s for s in students if s != '']
    students_lc = [x.lower() for x in students]

    return students, students_lc

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
    """
    Compute course statistics, including number of problems, videos, html.

    course is a CourseDescriptor from the xmodule system.
    """

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
    stats = dict(counts)  	# number of each kind of module
    return stats


def dump_grading_context(course):
    """
    Dump information about course grading context (eg which problems are graded in what assignments)
    Very useful for debugging grading_policy.json and policy.json
    """
    msg = "-----------------------------------------------------------------------------\n"
    msg += "Course grader:\n"

    msg += '%s\n' % course.grader.__class__
    graders = {}
    if isinstance(course.grader, xmgraders.WeightedSubsectionsGrader):
        msg += '\n'
        msg += "Graded sections:\n"
        for subgrader, category, weight in course.grader.sections:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n" % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += "-----------------------------------------------------------------------------\n"
    msg += "Listing grading context for course %s\n" % course.id

    gc = course.grading_context
    msg += "graded sections:\n"

    msg += '%s\n' % gc['graded_sections'].keys()
    for (gs, gsvals) in gc['graded_sections'].items():
        msg += "--> Section %s:\n" % (gs)
        for sec in gsvals:
            s = sec['section_descriptor']
            grade_format = getattr(s.lms, 'grade_format', None)
            aname = ''
            if grade_format in graders:
                g = graders[grade_format]
                aname = '%s %02d' % (g.short_label, g.index)
                g.index += 1
            elif s.display_name in graders:
                g = graders[s.display_name]
                aname = '%s' % g.short_label
            notes = ''
            if getattr(s, 'score_by_attempt', False):
                notes = ', score by attempt!'
            msg += "      %s (grade_format=%s, Assignment=%s%s)\n" % (s.display_name, grade_format, aname, notes)
    msg += "all descriptors:\n"
    msg += "length=%d\n" % len(gc['all_descriptors'])
    msg = '<pre>%s</pre>' % msg.replace('<', '&lt;')
    return msg


def get_background_task_table(course_id, problem_url, student=None):
    """
    Construct the "datatable" structure to represent background task history.

    Filters the background task history to the specified course and problem.
    If a student is provided, filters to only those tasks for which that student
    was specified.

    Returns a tuple of (msg, datatable), where the msg is a possible error message,
    and the datatable is the datatable to be used for display.
    """
    history_entries = get_instructor_task_history(course_id, problem_url, student)
    datatable = {}
    msg = ""
    # first check to see if there is any history at all
    # (note that we don't have to check that the arguments are valid; it
    # just won't find any entries.)
    if (history_entries.count()) == 0:
        if student is not None:
            template = '<font color="red">Failed to find any background tasks for course "{course}", module "{problem}" and student "{student}".</font>'
            msg += template.format(course=course_id, problem=problem_url, student=student.username)
        else:
            msg += '<font color="red">Failed to find any background tasks for course "{course}" and module "{problem}".</font>'.format(course=course_id, problem=problem_url)
    else:
        datatable['header'] = ["Task Type",
                               "Task Id",
                               "Requester",
                               "Submitted",
                               "Duration (sec)",
                               "Task State",
                               "Task Status",
                               "Task Output"]

        datatable['data'] = []
        for instructor_task in history_entries:
            # get duration info, if known:
            duration_sec = 'unknown'
            if hasattr(instructor_task, 'task_output') and instructor_task.task_output is not None:
                task_output = json.loads(instructor_task.task_output)
                if 'duration_ms' in task_output:
                    duration_sec = int(task_output['duration_ms'] / 1000.0)
            # get progress status message:
            success, task_message = get_task_completion_info(instructor_task)
            status = "Complete" if success else "Incomplete"
            # generate row for this task:
            row = [str(instructor_task.task_type),
                   str(instructor_task.task_id),
                   str(instructor_task.requester),
                   instructor_task.created.isoformat(' '),
                   duration_sec,
                   str(instructor_task.task_state),
                   status,
                   task_message]
            datatable['data'].append(row)

        if student is not None:
            datatable['title'] = "{course_id} > {location} > {student}".format(course_id=course_id,
                                                                               location=problem_url,
                                                                               student=student.username)
        else:
            datatable['title'] = "{course_id} > {location}".format(course_id=course_id, location=problem_url)

    return msg, datatable
