from openedx.core.djangoapps.models.course_details import CourseDetails
from lms.djangoapps.courseware.courses import get_course_by_id
from student.models import Registration
from util.json_request import JsonResponse
from util.request import safe_get_host
from common.lib.mandrill_client.client import MandrillClient


def get_course_details(course_id):
    course_descriptor = get_course_by_id(course_id)
    course = CourseDetails.populate(course_descriptor)
    return course


def send_account_activation_email(request, registration, user):
    activation_link = '{protocol}://{site}/activate/{key}'.format(
            protocol='https' if request.is_secure() else 'http',
            site=safe_get_host(request),
            key=registration.activation_key
        )

    context = {
        'first_name': user.first_name,
        'activation_link': activation_link,
    }
    MandrillClient().send_mail(MandrillClient.USER_ACCOUNT_ACTIVATION_TEMPLATE, user.email, context)


def reactivation_email_for_user_custom(request, user):
    try:
        reg = Registration.objects.get(user=user)
        send_account_activation_email(request, reg, user)
    except Registration.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('No inactive user with this e-mail exists'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme


def get_course_next_classes(request, course):
    """
    Method to get all upcoming reruns of a course
    """

    # imports to avoid circular dependencies
    import pytz
    from lms.djangoapps.courseware.courses import (
        get_course_by_id,
        get_permission_for_course_about,
        get_course_with_access
    )
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from lms.djangoapps.courseware.access import has_access
    from lms.djangoapps.courseware.views.views import registered_for_course
    from student.models import CourseEnrollment
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from course_action_state.models import CourseRerunState
    from datetime import datetime

    utc = pytz.UTC

    course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
    course_rerun_objects = CourseOverview.objects.select_related('image_set').filter(
        id__in=course_rerun_states, start__gte=datetime.utcnow().replace(tzinfo=utc)).order_by('start')

    course_next_classes = []

    for course in course_rerun_objects:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course.id.__str__())
        permission = get_permission_for_course_about()
        course = get_course_with_access(request.user, permission, course_key)
        registered = registered_for_course(course, request.user)

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = bool(has_access(request.user, 'enroll', course))
        invitation_only = course.invitation_only
        is_course_full = CourseEnrollment.objects.is_course_full(course)

        # Register button should be disabled if one of the following is true:
        # - Student is already registered for course
        # - Course is already full
        # - Student cannot enroll in course
        active_reg_button = not (registered or is_course_full or not can_enroll)

        course_next_classes.append({
            'user': request.user,
            'registered': registered,
            'is_course_full': is_course_full,
            'can_enroll': can_enroll,
            'invitation_only': invitation_only,
            'course': course,
            'active_reg_button': active_reg_button
        })
    return course_next_classes


def get_user_current_enrolled_class(request, course):
    """
    Method to get an ongoing user enrolled course. A course that meets the following criteria
    => start date <= today
    => end date > today
    => user is enrolled
    """

    import pytz
    from lms.djangoapps.courseware.courses import (
        get_permission_for_course_about,
        get_course_with_access
    )
    from datetime import datetime
    from django.core.urlresolvers import reverse
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from common.djangoapps.student.views import get_course_related_keys
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from student.models import CourseEnrollment
    from course_action_state.models import CourseRerunState
    utc = pytz.UTC

    all_course_reruns = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]

    current_class = CourseOverview.objects.select_related('image_set').filter(
        id__in=all_course_reruns, start__lte=datetime.utcnow().replace(tzinfo=utc),
        end__gt=datetime.utcnow().replace(tzinfo=utc)).order_by('-start').first()

    current_enrolled_class = False
    if current_class:
        current_enrolled_class = CourseEnrollment.is_enrolled(request.user, current_class.id)

    current_enrolled_class_target = ''
    if current_enrolled_class:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(current_class.id.__str__())
        permission = get_permission_for_course_about()
        current_class = get_course_with_access(request.user, permission, course_key)
        first_chapter_url, first_section = get_course_related_keys(request, current_class)
        current_enrolled_class_target = reverse('courseware_section',
                                                args=[current_class.id.to_deprecated_string(),
                                                      first_chapter_url, first_section])

    return current_enrolled_class, current_enrolled_class_target
