"""
Views related to the Custom Courses feature.
"""
import csv
import datetime
import functools
import json
import logging
import pytz

from copy import deepcopy
from cStringIO import StringIO

from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django_future.csrf import ensure_csrf_cookie  # pylint: disable=import-error
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from courseware.courses import get_course_by_id  # pylint: disable=import-error

from courseware.field_overrides import disable_overrides  # pylint: disable=import-error
from courseware.grades import iterate_grades_for  # pylint: disable=import-error
from courseware.model_data import FieldDataCache  # pylint: disable=import-error
from courseware.module_render import get_module_for_descriptor  # pylint: disable=import-error
from edxmako.shortcuts import render_to_response  # pylint: disable=import-error
from opaque_keys.edx.keys import CourseKey
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error

from instructor.offline_gradecalc import student_grades  # pylint: disable=import-error
from instructor.views.api import _split_input_list  # pylint: disable=import-error
from instructor.views.tools import get_student_from_identifier  # pylint: disable=import-error

from .models import CustomCourseForEdX, CcxMembership
from .overrides import (
    clear_override_for_ccx,
    get_override_for_ccx,
    override_field_for_ccx,
    ccx_context,
)
from .utils import (
    enroll_email,
    unenroll_email,
)
from ccx import ACTIVE_CCX_KEY  # pylint: disable=import-error


log = logging.getLogger(__name__)
TODAY = datetime.datetime.today  # for patching in tests


def coach_dashboard(view):
    """
    View decorator which enforces that the user have the CCX coach role on the
    given course and goes ahead and translates the course_id from the Django
    route into a course object.
    """
    @functools.wraps(view)
    def wrapper(request, course_id):
        """
        Wraps the view function, performing access check, loading the course,
        and modifying the view's call signature.
        """
        course_key = CourseKey.from_string(course_id)
        role = CourseCcxCoachRole(course_key)
        if not role.has_user(request.user):
            return HttpResponseForbidden(
                _('You must be a CCX Coach to access this view.'))
        course = get_course_by_id(course_key, depth=None)
        return view(request, course)
    return wrapper


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def dashboard(request, course):
    """
    Display the CCX Coach Dashboard.
    """
    ccx = get_ccx_for_coach(course, request.user)
    context = {
        'course': course,
        'ccx': ccx,
    }

    if ccx:
        schedule = get_ccx_schedule(course, ccx)
        grading_policy = get_override_for_ccx(
            ccx, course, 'grading_policy', course.grading_policy)
        context['schedule'] = json.dumps(schedule, indent=4)
        context['save_url'] = reverse(
            'save_ccx', kwargs={'course_id': course.id})
        context['ccx_members'] = CcxMembership.objects.filter(ccx=ccx)
        context['gradebook_url'] = reverse(
            'ccx_gradebook', kwargs={'course_id': course.id})
        context['grades_csv_url'] = reverse(
            'ccx_grades_csv', kwargs={'course_id': course.id})
        context['grading_policy'] = json.dumps(grading_policy, indent=4)
        context['grading_policy_url'] = reverse(
            'ccx_set_grading_policy', kwargs={'course_id': course.id})
    else:
        context['create_ccx_url'] = reverse(
            'create_ccx', kwargs={'course_id': course.id})
    return render_to_response('ccx/coach_dashboard.html', context)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def create_ccx(request, course):
    """
    Create a new CCX
    """
    name = request.POST.get('name')
    ccx = CustomCourseForEdX(
        course_id=course.id,
        coach=request.user,
        display_name=name)
    ccx.save()

    # Make sure start/due are overridden for entire course
    start = TODAY().replace(tzinfo=pytz.UTC)
    override_field_for_ccx(ccx, course, 'start', start)
    override_field_for_ccx(ccx, course, 'due', None)

    # Hide anything that can show up in the schedule
    hidden = 'visible_to_staff_only'
    for chapter in course.get_children():
        override_field_for_ccx(ccx, chapter, hidden, True)
        for sequential in chapter.get_children():
            override_field_for_ccx(ccx, sequential, hidden, True)
            for vertical in sequential.get_children():
                override_field_for_ccx(ccx, vertical, hidden, True)

    url = reverse('ccx_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def save_ccx(request, course):
    """
    Save changes to CCX.
    """
    ccx = get_ccx_for_coach(course, request.user)

    def override_fields(parent, data, graded, earliest=None):
        """
        Recursively apply CCX schedule data to CCX by overriding the
        `visible_to_staff_only`, `start` and `due` fields for units in the
        course.
        """
        blocks = {
            str(child.location): child
            for child in parent.get_children()}
        for unit in data:
            block = blocks[unit['location']]
            override_field_for_ccx(
                ccx, block, 'visible_to_staff_only', unit['hidden'])
            start = parse_date(unit['start'])
            if start:
                if not earliest or start < earliest:
                    earliest = start
                override_field_for_ccx(ccx, block, 'start', start)
            else:
                clear_override_for_ccx(ccx, block, 'start')
            due = parse_date(unit['due'])
            if due:
                override_field_for_ccx(ccx, block, 'due', due)
            else:
                clear_override_for_ccx(ccx, block, 'due')

            if not unit['hidden'] and block.graded:
                graded[block.format] = graded.get(block.format, 0) + 1

            children = unit.get('children', None)
            if children:
                override_fields(block, children, graded, earliest)
        return earliest

    graded = {}
    earliest = override_fields(course, json.loads(request.body), graded)
    if earliest:
        override_field_for_ccx(ccx, course, 'start', earliest)

    # Attempt to automatically adjust grading policy
    changed = False
    policy = get_override_for_ccx(
        ccx, course, 'grading_policy', course.grading_policy
    )
    policy = deepcopy(policy)
    grader = policy['GRADER']
    for section in grader:
        count = graded.get(section.get('type'), 0)
        if count < section['min_count']:
            changed = True
            section['min_count'] = count
    if changed:
        override_field_for_ccx(ccx, course, 'grading_policy', policy)

    return HttpResponse(
        json.dumps({
            'schedule': get_ccx_schedule(course, ccx),
            'grading_policy': json.dumps(policy, indent=4)}),
        content_type='application/json',
    )


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def set_grading_policy(request, course):
    """
    Set grading policy for the CCX.
    """
    ccx = get_ccx_for_coach(course, request.user)
    override_field_for_ccx(
        ccx, course, 'grading_policy', json.loads(request.POST['policy']))

    url = reverse('ccx_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


def validate_date(year, month, day, hour, minute):
    """
    avoid corrupting db if bad dates come in
    """
    valid = True
    if year < 0:
        valid = False
    if month < 1 or month > 12:
        valid = False
    if day < 1 or day > 31:
        valid = False
    if hour < 0 or hour > 23:
        valid = False
    if minute < 0 or minute > 59:
        valid = False
    return valid


def parse_date(datestring):
    """
    Generate a UTC datetime.datetime object from a string of the form
    'YYYY-MM-DD HH:MM'.  If string is empty or `None`, returns `None`.
    """
    if datestring:
        date, time = datestring.split(' ')
        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))
        if validate_date(year, month, day, hour, minute):
            return datetime.datetime(
                year, month, day, hour, minute, tzinfo=pytz.UTC)

    return None


def get_ccx_for_coach(course, coach):
    """
    Looks to see if user is coach of a CCX for this course.  Returns the CCX or
    None.
    """
    try:
        return CustomCourseForEdX.objects.get(
            course_id=course.id,
            coach=coach)
    except CustomCourseForEdX.DoesNotExist:
        return None


def get_ccx_schedule(course, ccx):
    """
    Generate a JSON serializable CCX schedule.
    """
    def visit(node, depth=1):
        """
        Recursive generator function which yields CCX schedule nodes.
        We convert dates to string to get them ready for use by the js date
        widgets, which use text inputs.
        """
        for child in node.get_children():
            start = get_override_for_ccx(ccx, child, 'start', None)
            if start:
                start = str(start)[:-9]
            due = get_override_for_ccx(ccx, child, 'due', None)
            if due:
                due = str(due)[:-9]
            hidden = get_override_for_ccx(
                ccx, child, 'visible_to_staff_only',
                child.visible_to_staff_only)
            visited = {
                'location': str(child.location),
                'display_name': child.display_name,
                'category': child.category,
                'start': start,
                'due': due,
                'hidden': hidden,
            }
            if depth < 3:
                children = tuple(visit(child, depth + 1))
                if children:
                    visited['children'] = children
                    yield visited
            else:
                yield visited

    with disable_overrides():
        return tuple(visit(course))


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_schedule(request, course):
    """
    get json representation of ccx schedule
    """
    ccx = get_ccx_for_coach(course, request.user)
    schedule = get_ccx_schedule(course, ccx)
    json_schedule = json.dumps(schedule, indent=4)
    return HttpResponse(json_schedule, mimetype='application/json')


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_invite(request, course):
    """
    Invite users to new ccx
    """
    ccx = get_ccx_for_coach(course, request.user)
    action = request.POST.get('enrollment-button')
    identifiers_raw = request.POST.get('student-ids')
    identifiers = _split_input_list(identifiers_raw)
    auto_enroll = True if 'auto-enroll' in request.POST else False
    email_students = True if 'email-students' in request.POST else False
    for identifier in identifiers:
        user = None
        email = None
        try:
            user = get_student_from_identifier(identifier)
        except User.DoesNotExist:
            email = identifier
        else:
            email = user.email
        try:
            validate_email(email)
            if action == 'Enroll':
                enroll_email(
                    ccx,
                    email,
                    auto_enroll=auto_enroll,
                    email_students=email_students
                )
            if action == "Unenroll":
                unenroll_email(ccx, email, email_students=email_students)
        except ValidationError:
            log.info('Invalid user name or email when trying to invite students: %s', email)
    url = reverse('ccx_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_student_management(request, course):
    """Manage the enrollment of individual students in a CCX
    """
    ccx = get_ccx_for_coach(course, request.user)
    action = request.POST.get('student-action', None)
    student_id = request.POST.get('student-id', '')
    user = email = None
    try:
        user = get_student_from_identifier(student_id)
    except User.DoesNotExist:
        email = student_id
    else:
        email = user.email

    try:
        validate_email(email)
        if action == 'add':
            # by decree, no emails sent to students added this way
            # by decree, any students added this way are auto_enrolled
            enroll_email(ccx, email, auto_enroll=True, email_students=False)
        elif action == 'revoke':
            unenroll_email(ccx, email, email_students=False)
    except ValidationError:
        log.info('Invalid user name or email when trying to enroll student: %s', email)

    url = reverse('ccx_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_gradebook(request, course):
    """
    Show the gradebook for this CCX.
    """
    # Need course module for overrides to function properly
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id)

    ccx = get_ccx_for_coach(course, request.user)
    with ccx_context(ccx):
        # The grading policy for the MOOC is probably already cached.  We need
        # to make sure we have the CCX grading policy loaded.
        course._field_data_cache = {}  # pylint: disable=protected-access
        course.set_grading_policy(course.grading_policy)

        enrolled_students = User.objects.filter(
            ccxmembership__ccx=ccx,
            ccxmembership__active=1
        ).order_by('username').select_related("profile")

        student_info = [
            {
                'username': student.username,
                'id': student.id,
                'email': student.email,
                'grade_summary': student_grades(student, request, course),
                'realname': student.profile.name,
            }
            for student in enrolled_students
        ]

        return render_to_response('courseware/gradebook.html', {
            'students': student_info,
            'course': course,
            'course_id': course.id,
            'staff_access': request.user.is_staff,
            'ordered_grades': sorted(
                course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True),
        })


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_grades_csv(request, course):
    """
    Download grades as CSV.
    """
    # Need course module for overrides to function properly
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id)
    ccx = get_ccx_for_coach(course, request.user)
    with ccx_context(ccx):
        # The grading policy for the MOOC is probably already cached.  We need
        # to make sure we have the CCX grading policy loaded.
        course._field_data_cache = {}  # pylint: disable=protected-access
        course.set_grading_policy(course.grading_policy)

        enrolled_students = User.objects.filter(
            ccxmembership__ccx=ccx,
            ccxmembership__active=1
        ).order_by('username').select_related("profile")
        grades = iterate_grades_for(course, enrolled_students)

        header = None
        rows = []
        for student, gradeset, __ in grades:
            if gradeset:
                # We were able to successfully grade this student for this
                # course.
                if not header:
                    # Encode the header row in utf-8 encoding in case there are
                    # unicode characters
                    header = [section['label'].encode('utf-8')
                              for section in gradeset[u'section_breakdown']]
                    rows.append(["id", "email", "username", "grade"] + header)

                percents = {
                    section['label']: section.get('percent', 0.0)
                    for section in gradeset[u'section_breakdown']
                    if 'label' in section
                }

                row_percents = [percents.get(label, 0.0) for label in header]
                rows.append([student.id, student.email, student.username,
                             gradeset['percent']] + row_percents)

        buf = StringIO()
        writer = csv.writer(buf)
        for row in rows:
            writer.writerow(row)

        return HttpResponse(buf.getvalue(), content_type='text/plain')


@login_required
def switch_active_ccx(request, course_id, ccx_id=None):
    """set the active CCX for the logged-in user
    """
    course_key = CourseKey.from_string(course_id)
    # will raise Http404 if course_id is bad
    course = get_course_by_id(course_key)
    course_url = reverse(
        'course_root', args=[course.id.to_deprecated_string()]
    )
    if ccx_id is not None:
        try:
            requested_ccx = CustomCourseForEdX.objects.get(pk=ccx_id)
            assert unicode(requested_ccx.course_id) == course_id
            if not CcxMembership.objects.filter(
                    ccx=requested_ccx, student=request.user, active=True
            ).exists():
                ccx_id = None
        except CustomCourseForEdX.DoesNotExist:
            # what to do here?  Log the failure?  Do we care?
            ccx_id = None
        except AssertionError:
            # what to do here?  Log the failure?  Do we care?
            ccx_id = None

    request.session[ACTIVE_CCX_KEY] = ccx_id

    return HttpResponseRedirect(course_url)
