"""Intercept login and registration requests.

This module contains legacy code originally from `student.views`.
"""
import re

from django.conf import settings
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
import external_auth.views

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey


# pylint: disable=fixme
# TODO: This function is kind of gnarly/hackish/etc and is only used in one location.
# It'd be awesome if we could get rid of it; manually parsing course_id strings form larger strings
# seems Probably Incorrect
def _parse_course_id_from_string(input_str):
    """
    Helper function to determine if input_str (typically the queryparam 'next') contains a course_id.
    @param input_str:
    @return: the course_id if found, None if not
    """
    m_obj = re.match(r'^/courses/{}'.format(settings.COURSE_ID_PATTERN), input_str)
    if m_obj:
        return CourseKey.from_string(m_obj.group('course_id'))
    return None


def _get_course_enrollment_domain(course_id):
    """
    Helper function to get the enrollment domain set for a course with id course_id
    @param course_id:
    @return:
    """
    course = modulestore().get_course(course_id)
    if course is None:
        return None

    return course.enrollment_domain


def login(request):
    """Allow external auth to intercept and handle a login request.

    Arguments:
        request (Request): A request for the login page.

    Returns:
        Response or None

    """
    # Default to a `None` response, indicating that external auth
    # is not handling the request.
    response = None

    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
        # Redirect to IONISx, we don't want the registration form.
        get = request.GET.copy()

        if 'course_id' in request.GET:
            request.session['enroll_course_id'] = request.GET.get('course_id')
            get.update({'next': reverse('about_course', kwargs={'course_id': unicode(request.GET.get('course_id'))})})

        redirect_uri = reverse('social:begin', args=('portal-oauth2',))
        response = external_auth.views.redirect_with_get(redirect_uri, get, do_reverse=False)

    elif settings.FEATURES['AUTH_USE_CERTIFICATES'] and external_auth.views.ssl_get_cert_from_request(request):
        # SSL login doesn't require a view, so redirect
        # branding and allow that to process the login if it
        # is enabled and the header is in the request.
        response = external_auth.views.redirect_with_get('root', request.GET)
    elif settings.FEATURES.get('AUTH_USE_CAS'):
        # If CAS is enabled, redirect auth handling to there
        response = redirect(reverse('cas-login'))
    elif settings.FEATURES.get('AUTH_USE_SHIB'):
        redirect_to = request.GET.get('next')
        if redirect_to:
            course_id = _parse_course_id_from_string(redirect_to)
            if course_id and _get_course_enrollment_domain(course_id):
                response = external_auth.views.course_specific_login(request, course_id.to_deprecated_string())

    return response


def register(request):
    """Allow external auth to intercept and handle a registration request.

    Arguments:
        request (Request): A request for the registration page.

    Returns:
        Response or None

    """
    response = None
    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
        # Redirect to IONISx, we don't want the registration form.
        get = request.GET.copy()

        if 'course_id' in request.GET:
            request.session['enroll_course_id'] = request.GET.get('course_id')
            get.update({'next': reverse('about_course', kwargs={'course_id': unicode(request.GET.get('course_id'))})})

        redirect_uri = reverse('social:begin', args=('portal-oauth2',))
        response = external_auth.views.redirect_with_get(redirect_uri, get, do_reverse=False)

    elif settings.FEATURES.get('AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP'):
        # Redirect to branding to process their certificate if SSL is enabled
        # and registration is disabled.
        response = external_auth.views.redirect_with_get('root', request.GET)
    return response
