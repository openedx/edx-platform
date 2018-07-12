import pytz
from datetime import datetime
from openedx.core.djangoapps.models.course_details import CourseDetails
from lms.djangoapps.courseware.courses import get_course_by_id
from student.models import Registration
from util.json_request import JsonResponse
from util.request import safe_get_host
from common.lib.mandrill_client.client import MandrillClient
utc = pytz.UTC


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


def has_access_custom(course):
    """ User can enroll if current time is between enrollment start and end date """
    current_time = datetime.utcnow().replace(tzinfo=utc)
    if not course.enrollment_start or not course.enrollment_end:
        return False

    if course.enrollment_start < current_time < course.enrollment_end:
        return True
    else:
        return False


def get_course_next_classes(request, course):
    """
    Method to get all upcoming reruns of a course
    """

    # imports to avoid circular dependencies
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from lms.djangoapps.courseware.access import _can_enroll_courselike
    from lms.djangoapps.courseware.views.views import registered_for_course
    from student.models import CourseEnrollment
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from course_action_state.models import CourseRerunState

    current_time = datetime.utcnow().replace(tzinfo=utc)
    course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
    course_rerun_objects = CourseOverview.objects.select_related('image_set').filter(
        id__in=course_rerun_states, start__gt=current_time).order_by('start')

    course_next_classes = []

    for _course in course_rerun_objects:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(_course.id.__str__())
        course = get_course_by_id(course_key)
        registered = registered_for_course(course, request.user)

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = _can_enroll_courselike(request.user, course)
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
            'can_enroll': can_enroll.has_access,
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
    from datetime import datetime
    from django.core.urlresolvers import reverse
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from common.djangoapps.student.views import get_course_related_keys
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from student.models import CourseEnrollment
    from course_action_state.models import CourseRerunState

    all_course_reruns = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
    current_time = datetime.utcnow().replace(tzinfo=utc)
    current_class = CourseOverview.objects.select_related('image_set').filter(
        id__in=all_course_reruns, start__lte=current_time, end__gte=current_time).order_by('-start').first()

    current_enrolled_class = False
    if current_class:
        current_enrolled_class = CourseEnrollment.is_enrolled(request.user, current_class.id)

    current_enrolled_class_target = ''
    if current_enrolled_class:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(current_class.id.__str__())
        current_class = get_course_by_id(course_key)
        first_chapter_url, first_section = get_course_related_keys(request, current_class)
        current_enrolled_class_target = reverse('courseware_section',
                                                args=[current_class.id.to_deprecated_string(),
                                                      first_chapter_url, first_section])

    return current_class, current_enrolled_class, current_enrolled_class_target
