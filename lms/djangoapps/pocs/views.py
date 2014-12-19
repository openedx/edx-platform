"""
Views related to the Personal Online Courses feature.
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
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from courseware.courses import get_course_by_id
from courseware.field_overrides import disable_overrides
from courseware.grades import iterate_grades_for
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.roles import CoursePocCoachRole

from instructor.offline_gradecalc import student_grades
from instructor.views.api import _split_input_list
from instructor.views.tools import get_student_from_identifier

from .models import PersonalOnlineCourse, PocMembership
from .overrides import (
    clear_override_for_poc,
    get_override_for_poc,
    override_field_for_poc,
    poc_context,
)
from .utils import (
    enroll_email,
    unenroll_email,
)
from pocs import ACTIVE_POC_KEY


log = logging.getLogger(__name__)
TODAY = datetime.datetime.today  # for patching in tests


def coach_dashboard(view):
    """
    View decorator which enforces that the user have the POC coach role on the
    given course and goes ahead and translates the course_id from the Django
    route into a course object.
    """
    @functools.wraps(view)
    def wrapper(request, course_id):
        """
        Wraps the view function, performing access check, loading the course,
        and modifying the view's call signature.
        """
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        role = CoursePocCoachRole(course_key)
        if not role.has_user(request.user):
            return HttpResponseForbidden(
                _('You must be a POC Coach to access this view.'))
        course = get_course_by_id(course_key, depth=None)
        return view(request, course)
    return wrapper


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def dashboard(request, course):
    """
    Display the POC Coach Dashboard.
    """
    poc = get_poc_for_coach(course, request.user)
    context = {
        'course': course,
        'poc': poc,
    }

    if poc:
        schedule = get_poc_schedule(course, poc)
        grading_policy = get_override_for_poc(
            poc, course, 'grading_policy', course.grading_policy)
        context['schedule'] = json.dumps(schedule, indent=4)
        context['save_url'] = reverse(
            'save_poc', kwargs={'course_id': course.id})
        context['poc_members'] = PocMembership.objects.filter(poc=poc)
        context['gradebook_url'] = reverse(
            'poc_gradebook', kwargs={'course_id': course.id})
        context['grades_csv_url'] = reverse(
            'poc_grades_csv', kwargs={'course_id': course.id})
        context['grading_policy'] = json.dumps(grading_policy, indent=4)
        context['grading_policy_url'] = reverse(
            'poc_set_grading_policy', kwargs={'course_id': course.id})
    else:
        context['create_poc_url'] = reverse(
            'create_poc', kwargs={'course_id': course.id})
    return render_to_response('pocs/coach_dashboard.html', context)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def create_poc(request, course):
    """
    Create a new POC
    """
    name = request.POST.get('name')
    poc = PersonalOnlineCourse(
        course_id=course.id,
        coach=request.user,
        display_name=name)
    poc.save()

    # Make sure start/due are overridden for entire course
    start = TODAY().replace(tzinfo=pytz.UTC)
    override_field_for_poc(poc, course, 'start', start)
    override_field_for_poc(poc, course, 'due', None)

    # Hide anything that can show up in the schedule
    hidden = 'visible_to_staff_only'
    for chapter in course.get_children():
        override_field_for_poc(poc, chapter, hidden, True)
        for sequential in chapter.get_children():
            override_field_for_poc(poc, sequential, hidden, True)
            for vertical in sequential.get_children():
                override_field_for_poc(poc, vertical, hidden, True)

    url = reverse('poc_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def save_poc(request, course):
    """
    Save changes to POC.
    """
    poc = get_poc_for_coach(course, request.user)

    def override_fields(parent, data, graded, earliest=None):
        """
        Recursively apply POC schedule data to POC by overriding the
        `visible_to_staff_only`, `start` and `due` fields for units in the
        course.
        """
        blocks = {
            str(child.location): child
            for child in parent.get_children()}
        for unit in data:
            block = blocks[unit['location']]
            override_field_for_poc(
                poc, block, 'visible_to_staff_only', unit['hidden'])
            start = parse_date(unit['start'])
            if start:
                if not earliest or start < earliest:
                    earliest = start
                override_field_for_poc(poc, block, 'start', start)
            else:
                clear_override_for_poc(poc, block, 'start')
            due = parse_date(unit['due'])
            if due:
                override_field_for_poc(poc, block, 'due', due)
            else:
                clear_override_for_poc(poc, block, 'due')

            if not unit['hidden'] and block.graded:
               graded[block.format] = graded.get(block.format, 0) + 1

            children = unit.get('children', None)
            if children:
                override_fields(block, children, graded, earliest)
        return earliest

    graded = {}
    earliest = override_fields(course, json.loads(request.body), graded)
    if earliest:
        override_field_for_poc(poc, course, 'start', earliest)

    # Attempt to automatically adjust grading policy
    changed = False
    policy = get_override_for_poc(
        poc, course, 'grading_policy', course.grading_policy
    )
    policy = deepcopy(policy)
    grader = policy['GRADER']
    for section in grader:
        count = graded.get(section.get('type'), 0)
        if count < section['min_count']:
            changed = True
            section['min_count'] = count
    if changed:
        override_field_for_poc(poc, course, 'grading_policy', policy)

    return HttpResponse(
        json.dumps({
            'schedule': get_poc_schedule(course, poc),
            'grading_policy': json.dumps(policy, indent=4)}),
        content_type='application/json',
    )


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def set_grading_policy(request, course):
    """
    Set grading policy for the POC.
    """
    poc = get_poc_for_coach(course, request.user)
    override_field_for_poc(
        poc, course, 'grading_policy', json.loads(request.POST['policy']))

    url = reverse('poc_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


def parse_date(datestring):
    """
    Generate a UTC datetime.datetime object from a string of the form
    'YYYY-MM-DD HH:MM'.  If string is empty or `None`, returns `None`.
    """
    if datestring:
        date, time = datestring.split(' ')
        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))
        return datetime.datetime(
            year, month, day, hour, minute, tzinfo=pytz.UTC)

    return None


def get_poc_for_coach(course, coach):
    """
    Looks to see if user is coach of a POC for this course.  Returns the POC or
    None.
    """
    try:
        return PersonalOnlineCourse.objects.get(
            course_id=course.id,
            coach=coach)
    except PersonalOnlineCourse.DoesNotExist:
        return None


def get_poc_schedule(course, poc):
    """
    Generate a JSON serializable POC schedule.
    """
    def visit(node, depth=1):
        """
        Recursive generator function which yields POC schedule nodes.
        """
        for child in node.get_children():
            start = get_override_for_poc(poc, child, 'start', None)
            if start:
                start = str(start)[:-9]
            due = get_override_for_poc(poc, child, 'due', None)
            if due:
                due = str(due)[:-9]
            hidden = get_override_for_poc(
                poc, child, 'visible_to_staff_only',
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
def poc_invite(request, course):
    """
    Invite users to new poc
    """
    poc = get_poc_for_coach(course, request.user)
    action = request.POST.get('enrollment-button')
    identifiers_raw = request.POST.get('student-ids')
    identifiers = _split_input_list(identifiers_raw)
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
                enroll_email(poc, email, email_students=True)
            if action == "Unenroll":
                unenroll_email(poc, email, email_students=True)
        except ValidationError:
            pass  # maybe log this?
    url = reverse('poc_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def poc_student_management(request, course):
    """Manage the enrollment of individual students in a POC
    """
    poc = get_poc_for_coach(course, request.user)
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
            enroll_email(poc, email, email_students=False)
        elif action == 'revoke':
            unenroll_email(poc, email, email_students=False)
    except ValidationError:
        pass  # XXX: log, report?

    url = reverse('poc_coach_dashboard', kwargs={'course_id': course.id})
    return redirect(url)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def poc_gradebook(request, course):
    """
    Show the gradebook for this POC.
    """
    # Need course module for overrides to function properly
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id)

    poc = get_poc_for_coach(course, request.user)
    with poc_context(poc):
        # The grading policy for the MOOC is probably already cached.  We need
        # to make sure we have the POC grading policy loaded.
        course._field_data_cache = {}  # pylint: disable=protected-access
        course.set_grading_policy(course.grading_policy)

        enrolled_students = User.objects.filter(
            pocmembership__poc=poc,
            pocmembership__active=1
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
def poc_grades_csv(request, course):
    """
    Download grades as CSV.
    """
    # Need course module for overrides to function properly
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id)
    poc = get_poc_for_coach(course, request.user)
    with poc_context(poc):
        # The grading policy for the MOOC is probably already cached.  We need
        # to make sure we have the POC grading policy loaded.
        course._field_data_cache = {}  # pylint: disable=protected-access
        course.set_grading_policy(course.grading_policy)

        enrolled_students = User.objects.filter(
            pocmembership__poc=poc,
            pocmembership__active=1
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
def swich_active_poc(request, course_id, poc_id=None):
    """set the active POC for the logged-in user
    """
    user = request.user
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    # will raise Http404 if course_id is bad
    course = get_course_by_id(course_key)
    course_url = reverse(
        'course_root', args=[course.id.to_deprecated_string()]
    )
    if poc_id is not None:
        try:
            requested_poc = PersonalOnlineCourse.objects.get(pk=poc_id)
            assert requested_poc.course_id.to_deprecated_string() == course_id
            if not PocMembership.objects.filter(
                poc=requested_poc, student=request.user, active=True
            ).exists():
                poc_id = None
        except PersonalOnlineCourse.DoesNotExist:
            # what to do here?  Log the failure?  Do we care?
            poc_id = None
        except AssertionError:
            # what to do here?  Log the failure?  Do we care?
            poc_id = None

    request.session[ACTIVE_POC_KEY] = poc_id

    return HttpResponseRedirect(course_url)
