"""
Utilities for edly app.
"""
import logging
from functools import partial
from datetime import datetime
from urllib.parse import urljoin, urlparse

import jwt
import waffle
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from edx_ace import ace
from edx_ace.recipient import Recipient
from student.message_types import CertificateGeneration
from student.models import CourseAccessRole
from student.roles import CourseInstructorRole, CourseStaffRole, GlobalCourseCreatorRole, GlobalStaff, UserBasedRole
from util.organizations_helpers import get_organizations
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore

from lms.djangoapps.branding.api import get_privacy_url, get_tos_and_honor_code_url
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.contentserver.caching import del_cached_content
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration.helpers import get_current_site_configuration
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings, get_current_site
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.edly.constants import ESSENTIALS, DEFAULT_COURSE_IMAGE, DEFAULT_COURSE_IMAGE_PATH
from openedx.features.edly.context_processor import Colour
from openedx.features.edly.models import EdlyMultiSiteAccess, EdlySubOrganization
from common.djangoapps.student.models import UserProfile

LOGGER = logging.getLogger(__name__)


def is_edly_sub_org_active(edly_sub_org):
    """
    Checks if the request EdlySubOrganization is enabled or disabled.

    Arguments:
        request: EdlySubOrganization model class

    Returns:
        bool: Returns True if site is enabled and False if the site is disabled.
    """

    return edly_sub_org.is_active


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

    if getattr(request.user, 'edly_multisite_user', None) is None:
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

    edly_org = edly_sub_org.edly_organization
    edly_slug = get_edly_org_from_cookie(edly_user_info_cookie)
    edly_access_user = request.user.edly_multisite_user.filter(
        Q(sub_org__lms_site=current_site) |
        Q(sub_org__studio_site=current_site) |
        Q(sub_org__preview_site=current_site)
    )

    if edly_access_user.exists() and edly_org.enable_all_edly_sub_org_login and edly_org.slug == edly_slug:
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


def get_edly_org_from_cookie(encoded_cookie_data):
    """
    Returns edly-org from the edly-user-info cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        string
    """

    if not encoded_cookie_data:
        return ''

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data['edly-org']


def get_edx_org_from_cookie(encoded_cookie_data):
    """
    Returns edx-orgs short name from the edly-user-info cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        list
    """

    if not encoded_cookie_data:
        return []

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data['edx-orgs']


def get_enabled_organizations(request):
    """
    Helper method to get linked organizations for request site.

    Returns:
        list: List of linked organizations for request site
    """

    if not waffle.switch_is_active(settings.ENABLE_EDLY_ORGANIZATIONS_SWITCH):
        return get_organizations()

    studio_site_edx_organizations = request.site.edly_sub_org_for_studio.edx_organizations.all()
    if not studio_site_edx_organizations:
        LOGGER.exception('No EdlySubOrganization found for site %s', request.site)

    return studio_site_edx_organizations.values()


def get_edly_sub_org_from_request(request):
    """
    Helper method to get edly sub organization from request object.

    Returns:
        EdlySubOrg: edly_sub_org object
    """
    try:
        edly_sub_org = request.site.edly_sub_org_for_lms
    except EdlySubOrganization.DoesNotExist:
        edly_sub_org = request.site.edly_sub_org_for_studio

    return edly_sub_org

def create_edly_access_role(request, user):
    """
    Create edly user link with edly multi site access.

    Arguments:
        request (WSGI Request): Django request object
        user (object): User object.

    Returns:
        object: EdlyMultiSiteAccess object.

    """
    edly_sub_org = get_edly_sub_org_from_request(request)
    edly_access_user, _ = EdlyMultiSiteAccess.objects.get_or_create(
        user=user,
        sub_org=edly_sub_org,
    )

    return edly_access_user


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
    edly_sub_org = get_edly_sub_org_from_request(request)
    is_edly_panel_admin_user = request_user.edly_multisite_user.get(
        sub_org=edly_sub_org
    ).groups.filter(name=settings.EDLY_PANEL_ADMIN_USERS_GROUP).exists()
    if not GlobalStaff().has_user(request_user) and not is_edly_panel_admin_user:
        raise PermissionDenied

    course_creator, __ = CourseCreator.objects.get_or_create(user=user)
    course_creator.state = CourseCreator.GRANTED if set_global_creator else CourseCreator.UNREQUESTED
    course_creator.note = 'Global course creator user was updated by panel admin {}'.format(request_user.email)
    course_creator.admin = request_user
    course_creator.save()
    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    edx_orgs = get_edx_org_from_cookie(edly_user_info_cookie)

    if not edx_orgs:
        edx_orgs = get_edly_sub_org_from_request(request)
        edx_orgs = [edx_orgs.slug]

    for edx_org in edx_orgs:
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
        user.edly_multisite_user.get(sub_org__lms_site=current_site)
        return True
    except EdlyMultiSiteAccess.DoesNotExist:
        return False


def edly_panel_user_has_edly_org_access(request):
    """
    Check if requesting user is an Edly panel user.
    """
    return request.user.edly_multisite_user.filter(
        sub_org__lms_site=request.site,
        groups__name__in=[
            settings.EDLY_PANEL_ADMIN_USERS_GROUP,
            settings.EDLY_PANEL_USERS_GROUP,
        ]
    ).exists()


def user_can_login_on_requested_edly_organization(request, user, current_site=None):
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

    if not current_site:
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

    edly_sub_orgs = EdlySubOrganization.objects.filter(
        edly_organization=edly_sub_org.edly_organization
    )

    return user.edly_multisite_user.filter(sub_org__in=edly_sub_orgs).count() > 0


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
    edx_orgs = get_edx_org_from_cookie(edly_user_info_cookie)

    filtered_courses = [course for course in list(all_courses) if course.org in edx_orgs]

    return filtered_courses


def create_learner_link_with_permission_groups(edly_access_user):
    """
    Create Edly Learner Link with Learners Permission Groups.

    Arguments:
        user (object): Edly Multi Site Access object.

    Returns:
        object: User object.

    """
    groups = [settings.EDLY_USER_ROLES.get('subscriber', None), settings.EDLY_USER_ROLES.get('panel_restricted', None)]
    groups_info = Group.objects.filter(name__in=groups)
    for new_group in groups_info:
        edly_access_user.groups.add(new_group)

    return edly_access_user


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


def get_logo_from_current_site_configurations():
    """
    Gets the "logo" value in "BRANDING" from current site configurations.

    Returns:
        dict: Context data.
    """
    context = dict()
    current_site_configuration = get_current_site_configuration()
    if current_site_configuration:
        context['logo_src'] = current_site_configuration.get_value('BRANDING', {}).get('logo', '')

    return context


def get_current_plan_from_site_configurations():
    """
    Gets the "CURRENT_PLAN" value in "DJANGO_SETTINGS_OVERRIDE" from current site configurations.

    Returns:
        str: current plan.
    """
    current_plan = ESSENTIALS
    current_site_configuration = get_current_site_configuration()
    if current_site_configuration:
        current_plan = current_site_configuration.get_value(
                'DJANGO_SETTINGS_OVERRIDE', {}).get('CURRENT_PLAN', ESSENTIALS)

    return current_plan


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

    if course_id.org in edly_sub_org.get_edx_organizations:
        return True

    LOGGER.info('Course organization does not match site organization')
    return False


def send_certificate_generation_email(msg, user, site):
    """
    Use edx_ace send() to deliver course certificate email based on user and site.
    """
    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(
            'Unable to send activation email to user from "{}" to "{}"'.format(
                msg.options['from_address'],
                user.email,
            )
        )


def compose_certificate_email(student, course, message_context):
    """
    Return message_context dict for course cerficate email.
    """
    message_context.update({
        'student_email': student.email,
        'student_name': student.profile.name,
        'course_name': course.display_name,
        'course_date': datetime.now().strftime('%m/%d/%Y'),
        'cert_url': '{}{}{}'.format(
            'http://' if settings.DEBUG else 'https://',
            message_context['lms_base'],
            message_context['cert_url'],
        ),
    })

    return message_context


def send_cert_email_to_course_staff(student_id, course_key, site_id, context_vars):
    """
    This celery task prepares context for course certificate email.
    """
    student = get_user_model().objects.get(id=student_id)
    course = modulestore().get_course(course_key, depth=0)
    site = Site.objects.get(id=site_id)

    access_roles = CourseAccessRole.objects.filter(
        org=course.org,
        course_id=course.id,
        user__is_active=True,
    ).values_list('user__id')

    instructors = get_user_model().objects.filter(id__in=access_roles)

    msg_context = compose_certificate_email(student, course, context_vars)

    for instructor in instructors:
        msg = CertificateGeneration(context=context_vars).personalize(
            recipient=Recipient(instructor.username, instructor.email),
            language=preferences_api.get_user_preference(student, LANGUAGE_KEY),
            user_context=msg_context,
        )
        msg.options['from_address'] = context_vars['contact_email']

        send_certificate_generation_email(msg, instructor, site)


def is_config_enabled(site, conf_key):
    """
    Returns if the given email is enabled or not.
    """
    site_conf = getattr(site, "configuration", None)
    if not site_conf:
        return True

    email_conf = site_conf.get_value('EMAILS_CONFIG', {})
    return email_conf.get(conf_key, True)


def get_message_context(site):
    """
    get template context for site.
    """
    message_context = get_base_template_context(site)
    color_dict = get_config_value_from_site_or_settings(
        'COLORS',
        site=site,
    )
    django_settings = get_config_value_from_site_or_settings(
        'DJANGO_SETTINGS_OVERRIDE',
        site=site,
    )

    primary_color = Colour(str(color_dict.get('primary')))

    message_context.update({
        'lms_base': django_settings.get('LMS_BASE'),
        'platform_name': django_settings.get('PLATFORM_NAME'),
        'edly_fonts_config': get_config_value_from_site_or_settings(
            'FONTS',
            site=site,
        ),
        'edly_branding_config': get_config_value_from_site_or_settings(
            'BRANDING',
            site=site,
        ),
        'edly_copyright_text': get_config_value_from_site_or_settings(
            'EDLY_COPYRIGHT_TEXT',
            site=site,
        ),
        'edly_colors_config': {'primary': primary_color},
    })

    return message_context


def get_value_from_django_settings_override(key, default=None, site=get_current_site()):
    """
    Gets the key value in "DJANGO_SETTINGS_OVERRIDE" from current site configurations.

    Returns:
        str: value.
    """
    value = default
    current_site_configuration = getattr(site, 'configuration', None)
    if current_site_configuration:
        value = current_site_configuration.get_value(
                'DJANGO_SETTINGS_OVERRIDE', {}).get(key, default)

    return value


def add_default_image_to_course_assets(course_key):
    """
    helper function to Add default image to course assets.
    """
    from django.contrib.staticfiles import finders
    content_location = StaticContent.compute_location(course_key, DEFAULT_COURSE_IMAGE)
    static_file = finders.find(DEFAULT_COURSE_IMAGE_PATH)
    if static_file:
        upload_file = open(static_file, "rb")

        static_content_partial = partial(StaticContent, content_location, DEFAULT_COURSE_IMAGE, 'image/jpg')

        content = static_content_partial(upload_file.read())
        temporary_file_path = None

        (thumbnail_content, thumbnail_location) = contentstore().generate_thumbnail(content,
                                                                                    tempfile_path=temporary_file_path)

        del_cached_content(thumbnail_location)

        if thumbnail_content is not None:
            content.thumbnail_location = thumbnail_location

        contentstore().save(content)
        del_cached_content(content.location)


def get_username_and_name_by_email(email):
    """
    helper function to return username if exists
    """
    user = get_user_model().objects.filter(email=email)
    if not user.exists():
        return {}
    
    user = user.first()
    userProfile = UserProfile.objects.filter(user=user)
    if userProfile.exists():
        userProfile = userProfile.first()
        return { "username": user.username, "name": userProfile.name }


def create_super_user_multisite_access(request, user, groups_names):
    """create an edly multisite access for a given user to all the organization sites"""
    edly_sub_org = get_edly_sub_org_from_request(request)
    sub_org = EdlySubOrganization.objects.filter(edly_organization=edly_sub_org.edly_organization)
    groups = Group.objects.filter(name__in=groups_names)
    
    for org in sub_org:
        edly_access_user, created = EdlyMultiSiteAccess.objects.get_or_create(
            user=user,
            sub_org=org
        )
        
        if created:
            for new_group in groups:
                edly_access_user.groups.add(new_group)


def create_user_access_role(request ,user ,groups_names):
    """create the user access role based on panel role"""
    panel_role = request.data.get('panel_role', None)
    if settings.EDLY_USER_ROLES.get(panel_role, None)==settings.EDLY_PANEL_SUPER_ADMIN:
        groups_names.append(settings.EDLY_PANEL_ADMIN_USERS_GROUP)
        create_super_user_multisite_access(request, user, groups_names)
    else:
        edly_access_user = create_edly_access_role(request, user)
        groups = Group.objects.filter(name__in=groups_names)
        for new_group in groups:
            edly_access_user.groups.add(new_group)
