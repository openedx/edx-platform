import logging

import jwt
import waffle
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.models import model_to_dict

from openedx.features.edly.models import EdlyUserProfile, EdlySubOrganization
from student import auth
from student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    GlobalCourseCreatorRole,
    GlobalStaff,
    UserBasedRole,
)
from util.organizations_helpers import get_organizations

LOGGER = logging.getLogger(__name__)


def user_has_edly_organization_access(request):
    """
    Check if the requested URL site is allowed for the user.

    This method checks if the requested URL site is in the requesting user's
    edly sub organizations list.

    Arguments:
        request: HTTP request object

    Returns:
        bool: Returns True if User has Edly Organization Access Otherwise False.
    """

    if getattr(request.user, 'edly_profile', None) is None:
        return False

    current_site = request.site

    try:
        edly_sub_org = EdlySubOrganization.objects.get(
            Q(lms_site=current_site) |
            Q(studio_site=current_site) |
            Q(preview_site=current_site)
        )
    except EdlySubOrganization.DoesNotExist:
        return False

    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    if edly_sub_org.slug == get_edly_sub_org_from_cookie(edly_user_info_cookie):
        return True

    return False


def encode_edly_user_info_cookie(cookie_data):
    """
    Encode edly_user_info cookie data into JWT string.

    Arguments:
        cookie_data (dict): Edly user info cookie dict.

    Returns:
        string
    """
    return jwt.encode(cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM)


def decode_edly_user_info_cookie(encoded_cookie_data):
    """
    Decode edly_user_info cookie data from JWT string.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        dict
    """
    return jwt.decode(encoded_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithms=[settings.EDLY_JWT_ALGORITHM])


def get_edly_sub_org_from_cookie(encoded_cookie_data):
    """
    Returns edly-sub-org slug from the edly-user-info cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        string
    """

    if not encoded_cookie_data:
        return ''

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data['edly-sub-org']


def get_edx_org_from_cookie(encoded_cookie_data):
    """
    Returns edx-org short name from the edly-user-info cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        string
    """

    if not encoded_cookie_data:
        return ''

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data['edx-org']


def get_enabled_organizations(request):
    """
    Helper method to get linked organizations for request site.

    Returns:
        list: List of linked organizations for request site
    """

    if not waffle.switch_is_active(settings.ENABLE_EDLY_ORGANIZATIONS_SWITCH):
        return get_organizations()

    try:
        studio_site_edx_organization = model_to_dict(request.site.edly_sub_org_for_studio.edx_organization)
    except EdlySubOrganization.DoesNotExist:
        LOGGER.exception('No EdlySubOrganization found for site %s', request.site)
        return []

    return [studio_site_edx_organization]


def create_user_link_with_edly_sub_organization(request, user):
    """
    Create edly user profile link with edly sub organization.

    Arguments:
        request (WSGI Request): Django request object
        user (object): User object.

    Returns:
        object: EdlyUserProfile object.

    """
    try:
        edly_sub_org = request.site.edly_sub_org_for_lms
    except EdlySubOrganization.DoesNotExist:
        edly_sub_org = request.site.edly_sub_org_for_studio
    edly_user_profile, __ = EdlyUserProfile.objects.get_or_create(user=user)
    edly_user_profile.edly_sub_organizations.add(edly_sub_org)
    edly_user_profile.save()

    return edly_user_profile


def update_course_creator_status(request_user, user, set_creator):
    """
    Updates course creator status of a user.
    """
    from course_creators.models import CourseCreator
    from course_creators.views import update_course_creator_group

    course_creator, __ = CourseCreator.objects.get_or_create(user=user)
    course_creator.state = CourseCreator.GRANTED if set_creator else CourseCreator.UNREQUESTED
    course_creator.note = 'Course creator user was updated by panel admin {}'.format(request_user.email)
    course_creator.admin = request_user
    course_creator.save()
    if not set_creator:
        update_course_creator_group(request_user, user, set_creator)
        instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
        staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
        instructor_courses_keys = [course.course_id for course in instructor_courses]
        staff_courses_keys = [course.course_id for course in staff_courses]
        UserBasedRole(user, CourseInstructorRole.ROLE).remove_courses(*instructor_courses_keys)
        UserBasedRole(user, CourseStaffRole.ROLE).remove_courses(*staff_courses_keys)


def set_global_course_creator_status(request, user, set_global_creator):
    """
    Updates global course creator status of a user.
    """
    from course_creators.models import CourseCreator

    request_user = request.user
    is_edly_panel_admin_user = request_user.groups.filter(name=settings.EDLY_PANEL_ADMIN_USERS_GROUP).exists()
    if not GlobalStaff().has_user(request_user) and not is_edly_panel_admin_user:
        raise PermissionDenied

    course_creator, __ = CourseCreator.objects.get_or_create(user=user)
    course_creator.state = CourseCreator.GRANTED if set_global_creator else CourseCreator.UNREQUESTED
    course_creator.note = 'Global course creator user was updated by panel admin {}'.format(request_user.email)
    course_creator.admin = request_user
    course_creator.save()
    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    edx_org = get_edx_org_from_cookie(edly_user_info_cookie)
    if set_global_creator:
        GlobalCourseCreatorRole(edx_org).add_users(user)
    else:
        GlobalCourseCreatorRole(edx_org).remove_users(user)


def user_belongs_to_edly_organization(request, user):
    """
    Check if user belongs to the requested URL site.

    Arguments:
        request: HTTP request object,
        user (object): User object.

    Returns:
        bool: Returns True if User belongs to Edly Organization Otherwise False.
    """

    current_site = request.site
    try:
        edly_sub_org = EdlySubOrganization.objects.get(
            Q(lms_site=current_site) |
            Q(studio_site=current_site) |
            Q(preview_site=current_site)
        )
    except EdlySubOrganization.DoesNotExist:
        return False

    if edly_sub_org.slug in user.edly_profile.get_linked_edly_sub_organizations:
        return True

    return False
