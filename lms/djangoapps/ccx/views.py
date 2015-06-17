"""
Views related to the Custom Courses feature.
"""
import csv
import datetime
import functools
import json
import logging
import pytz

from contextlib import contextmanager
from copy import deepcopy
from cStringIO import StringIO

from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from courseware.courses import get_course_by_id  # pylint: disable=import-error

from courseware.field_overrides import disable_overrides  # pylint: disable=import-error
from courseware.grades import iterate_grades_for  # pylint: disable=import-error
from courseware.model_data import FieldDataCache  # pylint: disable=import-error
from courseware.module_render import get_module_for_descriptor  # pylint: disable=import-error
from edxmako.shortcuts import render_to_response  # pylint: disable=import-error
from opaque_keys.edx.keys import CourseKey
from ccx_keys.locator import CCXLocator
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error

from instructor.offline_gradecalc import student_grades  # pylint: disable=import-error
from instructor.views.api import _split_input_list  # pylint: disable=import-error
from instructor.views.tools import get_student_from_identifier  # pylint: disable=import-error

from .models import CustomCourseForEdX, CcxMembership
from .overrides import (
    clear_override_for_ccx,
    get_override_for_ccx,
    override_field_for_ccx,
)
from .utils import (
    enroll_email,
    unenroll_email,
)


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
        ccx = None
        if isinstance(course_key, CCXLocator):
            ccx_id = course_key.ccx
            ccx = CustomCourseForEdX.objects.get(pk=ccx_id)
            course_key = ccx.course_id

        role = CourseCcxCoachRole(course_key)
        if not role.has_user(request.user):
            return HttpResponseForbidden(
                _('You must be a CCX Coach to access this view.'))

        course = get_course_by_id(course_key, depth=None)

        # if there is a ccx, we must validate that it is the ccx for this coach
        if ccx is not None:
            coach_ccx = get_ccx_for_coach(course, request.user)
            if coach_ccx is None or coach_ccx.id != ccx.id:
                return HttpResponseForbidden(
                    _('You must be the coach for this ccx to access this view')
                )

        return view(request, course, ccx)
    return wrapper


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def dashboard(request, course, ccx=None):
    """
    Display the CCX Coach Dashboard.
    """
    # right now, we can only have one ccx per user and course
    # so, if no ccx is passed in, we can sefely redirect to that
    if ccx is None:
        ccx = get_ccx_for_coach(course, request.user)
        if ccx:
            url = reverse(
                'ccx_coach_dashboard',
                kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)}
            )
            return redirect(url)

    context = {
        'course': course,
        'ccx': ccx,
    }

    if ccx:
        ccx_locator = CCXLocator.from_course_locator(course.id, ccx.id)
        schedule = get_ccx_schedule(course, ccx)
        grading_policy = get_override_for_ccx(
            ccx, course, 'grading_policy', course.grading_policy)
        context['schedule'] = json.dumps(schedule, indent=4)
        context['save_url'] = reverse(
            'save_ccx', kwargs={'course_id': ccx_locator})
        context['ccx_members'] = CcxMembership.objects.filter(ccx=ccx)
        context['gradebook_url'] = reverse(
            'ccx_gradebook', kwargs={'course_id': ccx_locator})
        context['grades_csv_url'] = reverse(
            'ccx_grades_csv', kwargs={'course_id': ccx_locator})
        context['grading_policy'] = json.dumps(grading_policy, indent=4)
        context['grading_policy_url'] = reverse(
            'ccx_set_grading_policy', kwargs={'course_id': ccx_locator})
    else:
        context['create_ccx_url'] = reverse(
            'create_ccx', kwargs={'course_id': course.id})
    return render_to_response('ccx/coach_dashboard.html', context)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def create_ccx(request, course, ccx=None):
    """
    Create a new CCX
    """
    name = request.POST.get('name')

    # prevent CCX objects from being created for deprecated course ids.
    if course.id.deprecated:
        messages.error(request, _(
            "You cannot create a CCX from a course using a deprecated id. "
            "Please create a rerun of this course in the studio to allow "
            "this action."))
        url = reverse('ccx_coach_dashboard', kwargs={'course_id', course.id})
        return redirect(url)

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

    ccx_id = CCXLocator.from_course_locator(course.id, ccx.id)  # pylint: disable=no-member
    url = reverse('ccx_coach_dashboard', kwargs={'course_id': ccx_id})
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def save_ccx(request, course, ccx=None):
    """
    Save changes to CCX.
    """
    if not ccx:
        raise Http404

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
def set_grading_policy(request, course, ccx=None):
    """
    Set grading policy for the CCX.
    """
    if not ccx:
        raise Http404

    override_field_for_ccx(
        ccx, course, 'grading_policy', json.loads(request.POST['policy']))

    url = reverse(
        'ccx_coach_dashboard',
        kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)}
    )
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
    ccxs = CustomCourseForEdX.objects.filter(
        course_id=course.id,
        coach=coach
    )
    # XXX: In the future, it would be nice to support more than one ccx per
    # coach per course.  This is a place where that might happen.
    if ccxs.exists():
        return ccxs[0]
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
def ccx_schedule(request, course, ccx=None):  # pylint: disable=unused-argument
    """
    get json representation of ccx schedule
    """
    if not ccx:
        raise Http404

    schedule = get_ccx_schedule(course, ccx)
    json_schedule = json.dumps(schedule, indent=4)
    return HttpResponse(json_schedule, mimetype='application/json')


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_invite(request, course, ccx=None):
    """
    Invite users to new ccx
    """
    if not ccx:
        raise Http404

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
    url = reverse(
        'ccx_coach_dashboard',
        kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)}
    )
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_student_management(request, course, ccx=None):
    """Manage the enrollment of individual students in a CCX
    """
    if not ccx:
        raise Http404

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

    url = reverse(
        'ccx_coach_dashboard',
        kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)}
    )
    return redirect(url)


@contextmanager
def ccx_course(ccx_locator):
    """Create a context in which the course identified by course_locator exists
    """
    course = get_course_by_id(ccx_locator)
    yield course


def prep_course_for_grading(course, request):
    """Set up course module for overrides to function properly"""
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id, course=course
    )

    course._field_data_cache = {}  # pylint: disable=protected-access
    course.set_grading_policy(course.grading_policy)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def ccx_gradebook(request, course, ccx=None):
    """
    Show the gradebook for this CCX.
    """
    if not ccx:
        raise Http404

    ccx_key = CCXLocator.from_course_locator(course.id, ccx.id)
    with ccx_course(ccx_key) as course:
        prep_course_for_grading(course, request)

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
def ccx_grades_csv(request, course, ccx=None):
    """
    Download grades as CSV.
    """
    if not ccx:
        raise Http404

    ccx_key = CCXLocator.from_course_locator(course.id, ccx.id)
    with ccx_course(ccx_key) as course:
        prep_course_for_grading(course, request)

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
