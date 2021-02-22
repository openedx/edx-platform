import logging
from urllib.parse import urljoin

import jwt
import waffle
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.branding.api import get_privacy_url, get_tos_and_honor_code_url
from openedx.core.djangoapps.site_configuration.helpers import get_current_site_configuration
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

    if request.user.is_superuser or request.user.is_staff:
        return True

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
    return jwt.encode(
        cookie_data,
        settings.EDLY_COOKIE_SECRET_KEY,
        algorithm=settings.EDLY_JWT_ALGORITHM
    ).decode('utf-8')


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


def user_belongs_to_edly_sub_organization(request, user):
    """
    Check if user belongs to the requested URL site.

    Arguments:
        request: HTTP request object,
        user (object): User object.

    Returns:
        bool: Returns True if User belongs to Edly Sub-organization Otherwise False.
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


def edly_panel_user_has_edly_org_access(request):
    """
    Check if requesting user is an Edly panel user.
    """
    return EdlyUserProfile.objects.filter(
        edly_sub_organizations__lms_site=request.site,
        user=request.user,
        user__groups__name__in=[
            settings.EDLY_PANEL_ADMIN_USERS_GROUP,
            settings.EDLY_PANEL_USERS_GROUP,
        ]
    ).exists()


def user_can_login_on_requested_edly_organization(request, user):
    """
    Check if user can login on the requested URL site.

    A user can be linked with only one edly organization (parent
    organization) but can be linked with its multiple edly sub
    organizations.

    A user can login on all edly sub organizations given that the parent
    edly organization has enabled "enable_all_edly_sub_org_login" field.

    Arguments:
        request: HTTP request object,
        user (object): User object.

    Returns:
        bool: Returns True if User can login, False otherwise
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

    if not edly_sub_org.edly_organization.enable_all_edly_sub_org_login:
        return False

    current_edly_org_slug_of_user = None
    edly_sub_org_of_user = user.edly_profile.edly_sub_organizations.first()
    if edly_sub_org_of_user:
        current_edly_org_slug_of_user = edly_sub_org_of_user.edly_organization.slug

    if current_edly_org_slug_of_user == edly_sub_org.edly_organization.slug:
        return True

    return False


def filter_courses_based_on_org(request, all_courses):
    """
    Filter courses based on the requested URL site.

    Most of our LMS based roles are not organization based we would
    need to filter courses manually based on org of current site.

    Arguments:
        request: HTTP request object,
        all_courses (iterator): Iterator object.

    Returns:
        list: Returns List of courses filtered based on current site organization.
    """

    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    edx_org = get_edx_org_from_cookie(edly_user_info_cookie)

    filtered_courses = [course for course in list(all_courses) if course.org == edx_org]

    return filtered_courses


def create_learner_link_with_permission_groups(user):
    """
    Create Edly Learner Link with Learners Permission Groups.

    Arguments:
        user (object): User object.

    Returns:
        object: User object.

    """
    groups = [settings.EDLY_USER_ROLES.get('subscriber', None), settings.EDLY_USER_ROLES.get('panel_restricted', None)]
    groups_info = Group.objects.filter(name__in=groups)
    for new_group in groups_info:
        user.groups.add(new_group)

    return user


def get_current_site_invalid_certificate_context(default_html_certificate_configuration):
    """
    Gets current site's context data for invalid certificate.

    Try to get current site's context data for invalid certificate from site configuration
    or fallback to empty urls.

    Arguments:
        default_html_certificate_configuration (dict): Default html configurations dict.

    Returns:
        dict: Context data.
    """
    context = dict(default_html_certificate_configuration.get('default'))
    current_site_configuration = get_current_site_configuration()

    if not current_site_configuration:
        return context

    context['platform_name'] = current_site_configuration.get_value('platform_name', settings.PLATFORM_NAME)
    context['logo_src'] = current_site_configuration.get_value('BRANDING', {}).get('logo', '')
    logo_redirect_url = settings.LMS_ROOT_URL
    context['logo_url'] = logo_redirect_url
    context['company_privacy_url'] = get_privacy_url()
    context['company_tos_url'] = get_tos_and_honor_code_url()
    return context

def clean_django_settings_override(django_settings_override):
    """
    Enforce only allowed django settings to be overridden.
    """
    if not django_settings_override:
        return

    django_settings_override_keys = django_settings_override.keys()
    disallowed_override_keys = list(set(django_settings_override_keys) - set(settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE))
    updated_override_keys = list(set(django_settings_override_keys) - set(disallowed_override_keys))
    missing_override_keys = list(set(settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE) - set(updated_override_keys))

    validation_errors = []
    if disallowed_override_keys:
        disallowed_override_keys_string = ', '.join(disallowed_override_keys)
        validation_errors.append(
            ValidationError(
                _('Django settings override(s) "%(disallowed_override_keys)s" is/are not allowed to be overridden.'),
                params={'disallowed_override_keys': disallowed_override_keys_string},
            )
        )

    if missing_override_keys:
        missing_override_keys_string = ', '.join(missing_override_keys)
        validation_errors.append(
            ValidationError(
                _('Django settings override(s) "%(missing_override_keys)s" is/are missing.'),
                params={'missing_override_keys': missing_override_keys_string},
            )
        )

    if validation_errors:
        raise ValidationError(validation_errors)


def get_marketing_link(marketing_urls, name):
    """
    Returns the correct URL for a link to the marketing site
    """
    if name in marketing_urls:
        return urljoin(marketing_urls.get('ROOT'), marketing_urls.get(name))
    else:
        LOGGER.warning("Cannot find corresponding link for name: %s", name)
        return ''


def is_course_org_same_as_site_org(site, course_id):
    """
    Check if the course organization matches with the site organization.
    """
    try:
        edly_sub_org = EdlySubOrganization.objects.get(lms_site=site)
    except EdlySubOrganization.DoesNotExist:
        LOGGER.info('No Edly sub organization found for site %s', site)
        return False

    if edly_sub_org.edx_organization.short_name == course_id.org:
        return True

    LOGGER.info('Course organization does not match site organization')
    return False
