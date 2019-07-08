from ipware.ip import get_ip
from opaque_keys import InvalidKeyError
from w3lib.url import add_or_replace_parameter

from django.core.urlresolvers import reverse

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.embargo import api as embargo_api
from student.models import CourseEnrollment
from openedx.features.course_card.helpers import get_related_card_id


def enroll_after_survey_completion(request):

    """
    This function return if appropriate parameters are being passed to enroll user after
    completion of mandatory surveys
    :param request:
    :return:
    """
    return bool(request.GET.get('course_id')) and bool(request.GET.get('enrollment_action'))


def enroll_in_course(request, next_url):

    if not enroll_after_survey_completion(request):
        return next_url

    action = request.GET.get('enrollment_action')
    course_id = request.GET.get('course_id')


    try:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        course_card_id = get_related_card_id(course_id)
    except InvalidKeyError:
        return next_url

    if action == "enroll":
        user = request.user
        # Make sure the course exists
        # We don't do this check on unenroll, or a bad course id can't be unenrolled from
        if not modulestore().has_course(course_id):
            return next_url

        # Check whether the user is blocked from enrolling in this course
        # This can occur if the user's IP is on a global blacklist
        # or if the user is enrolling in a country in which the course
        # is not available.
        redirect_url = embargo_api.redirect_if_blocked(
            course_id, user=user, ip_address=get_ip(request),
            url=request.path
        )
        if redirect_url:
            return redirect_url

        try:
            CourseEnrollment.enroll(user, course_id, check_access=True)
        except Exception as e:  # pylint: disable=broad-except
            return next_url

        course_target = reverse('about_course', args=[unicode(course_card_id)])
        course_target = add_or_replace_parameter(course_target, 'enrolled', '1')

        return course_target

    return next_url


def next_survey_url_with_enroll_params(next_step_url, request):
    if not enroll_after_survey_completion(request):
        return next_step_url

    url = add_or_replace_parameter(reverse(next_step_url),
                                   'course_id', request.GET.get('course_id'))
    url = add_or_replace_parameter(url, 'enrollment_action', request.GET.get('enrollment_action'))

    return url
