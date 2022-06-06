from datetime import timedelta

import beeline
import json

from urllib.parse import urlparse

import cssutils
import os
import sass

from django.db.models import Q, F
from django.utils import timezone
from django.core.files.storage import get_storage_class
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauth2_provider.generators import generate_client_id

from django.utils.text import slugify

from organizations import api as org_api
from organizations import models as org_models
from organizations.models import UserOrganizationMapping, Organization
from tahoe_sites.api import create_tahoe_site_by_link

from openedx.core.lib.api.api_key_permissions import is_request_has_valid_api_key
from openedx.core.lib.log_utils import audit_log
from openedx.core.djangoapps.theming.helpers import get_current_request, get_current_site
from openedx.core.djangoapps.theming.models import SiteTheme


@beeline.traced(name="get_lms_link_from_course_key")
def get_lms_link_from_course_key(base_lms_url, course_key):
    """
    Returns the microsite-aware LMS link based on the organization the course
    belongs to. If there is a Custom Domain in use, will return the custom
    domain URL instead.
    """
    beeline.add_context_field("base_lms_url", base_lms_url)
    beeline.add_context_field("course_key", course_key)
    # avoid circular import
    from openedx.core.djangoapps.appsembler.api.sites import get_site_for_course
    course_site = get_site_for_course(course_key)
    if course_site:
        return course_site.domain
    return base_lms_url


def _get_active_tiers_uuids():
    """
    Get active Tier organiation UUIDs from the Tiers (AMC Postgres) database.

    Note: This mostly a hack that's needed for improving the performance of
          batch operations by excluding dead sites.

    TODO: This helper should live in a future Tahoe Sites package.
    """
    from tiers.models import Tier
    # This queries the AMC Postgres database
    active_tiers_uuids = Tier.objects.filter(
        Q(tier_enforcement_exempt=True) |
        Q(tier_expires_at__gte=timezone.now())
    ).annotate(
        organization_edx_uuid=F('organization__edx_uuid')
    ).values_list('organization_edx_uuid', flat=True)
    return active_tiers_uuids


def get_active_organizations():
    """
    Get active organizations based on Tiers information.

    Note: This mostly a hack that's needed for improving the performance of
          batch operations by excluding dead sites.

    TODO: This helper should live in a future Tahoe Sites package.
    """
    active_tiers_uuids = _get_active_tiers_uuids()

    # Now back to the LMS MySQL database
    return Organization.objects.filter(
        edx_uuid__in=[str(edx_uuid) for edx_uuid in active_tiers_uuids],
    )


def get_active_sites(order_by='domain'):
    """
    Get active sites based on Tiers information.

    Note: This mostly a hack that's needed for improving the performance of
          batch operations by excluding dead sites.

    TODO: This helper should live in a future Tahoe Sites package.
    """
    return Site.objects.filter(
        organizations__in=get_active_organizations()
    ).order_by(order_by)


@beeline.traced(name="get_amc_oauth_app")
def get_amc_oauth_app():
    """
    Return the AMC OAuth2 Client model instance.
    """
    return Application.objects.get(client_id=settings.AMC_APP_OAUTH2_CLIENT_ID)


@beeline.traced(name="get_amc_tokens")
def get_amc_tokens(user):
    """
    Return the the access and refresh token with expiry date in a dict.

    TODO: we need to fix this. Can't be returning empty string tokens
    But then we need to rework the callers to handle errors. One is the
    admin iterface, so we have to rewrite some of the form handling there
    And there's a Django management command, so need to add error handling
    there. There may be other places
    """
    app = get_amc_oauth_app()
    tokens = {
        'access_token': '',
        'access_expires': '',
        'refresh_token': '',
    }

    try:
        access = AccessToken.objects.get(user=user, application=app)
        tokens.update({
            'access_token': access.token,
            'access_expires': access.expires,
        })
    except AccessToken.DoesNotExist:
        return tokens

    try:
        refresh = RefreshToken.objects.get(user=user, access_token=access, application=app)
        tokens['refresh_token'] = refresh.token
    except RefreshToken.DoesNotExist:
        pass

    return tokens


@beeline.traced(name="reset_amc_token")
def reset_amc_tokens(user, access_token=None, refresh_token=None):
    """
    Create and return new tokens, or extend existing ones to one year in the future.

    The `generate_client_id` function generates a 40 char hash
    This is longer than the implementaion in Hawthorn which generated 32 char hashes
    This function is used because it's there in the toolkit code rather than
    write a custom hash creation function to generates 32 chars
    """
    app = get_amc_oauth_app()
    valid_days = getattr(settings, 'OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS', 365)
    one_year_ahead = timezone.now() + timedelta(days=valid_days)

    access, _created = AccessToken.objects.get_or_create(
        user=user,
        application=app,
        defaults={
            'expires': one_year_ahead,
            'token': generate_client_id(),
        }
    )

    access.expires = one_year_ahead
    if access_token:
        access.token = access_token
    access.save()

    refresh, _created = RefreshToken.objects.get_or_create(
        user=user,
        access_token=access,
        application=app,
        defaults={
            'token': generate_client_id(),
        }
    )

    if refresh_token:
        refresh.token = refresh_token
    refresh.expired = False
    refresh.save()

    return get_amc_tokens(user)


@beeline.traced(name="make_amc_admin")
def make_amc_admin(user, org_name):
    """
    Make a user AMC admin with the following steps:

      - Reset organization and association.
      - Reset access and reset tokens, and set the expire one year ahead.
      - Return the recent tokens.
    """
    org = Organization.objects.get(Q(name=org_name) | Q(short_name=org_name))

    uom, _ = UserOrganizationMapping.objects.get_or_create(user=user, organization=org)
    uom.is_active = True
    uom.is_amc_admin = True
    uom.save()

    return {
        'user_email': user.email,
        'organization_name': org.name,
        'tokens': reset_amc_tokens(user),
    }


def to_safe_file_name(url):
    path = urlparse(url).path.lower()
    safe_extensions = {'.png', '.jpeg', '.jpg'}
    sluggified = slugify(path)

    for ext in safe_extensions:
        if path.endswith(ext):
            return sluggified + ext

    return sluggified


@beeline.traced(name="is_request_for_amc_admin")
def is_request_for_amc_admin(request):
    """
    Verifies the user is being made on behalf of AMC admin.
    """
    if not request or not request.method == 'POST':
        # Handle all no-request and non-registration requests gracefully.
        return False

    param = request.POST.get('registered_from_amc', False)
    has_amc_parameter = (param == 'True') or (param == 'true') or (param is True)

    if has_amc_parameter:
        if is_request_has_valid_api_key(request):
            # Security: Ensure the request is coming from the AMC backend with proper `X_EDX_API_KEY` header.
            return True
        else:
            audit_log('Suspicious call for the `is_request_for_amc_admin()` function.')
            raise Exception('Suspicious call for the `is_request_for_amc_admin()` function.')

    return False


@beeline.traced(name="get_current_organization")
def get_current_organization(failure_return_none=False):
    """
    Get current organization from request using multiple strategies.

    The split is made to enable global patching of the function.
    """
    return _get_current_organization(failure_return_none)


def _get_current_organization(failure_return_none=False):
    """
    Implements get_current_organization.
    """
    request = get_current_request()
    organization_name = None
    current_org = None

    if request:
        organization_name = request.POST.get('organization')
    elif not failure_return_none:
        raise Exception('get_current_organization: No request was found. Unable to get current organization.')

    if is_request_for_amc_admin(request) and organization_name:
        # This might raise DoesNotExist, it means that we are calling in a wrong way. So we should check
        # if `is_request_for_new_amc_site()` first instead of calling this function.
        try:
            current_org = Organization.objects.get(name=organization_name)
        except Organization.DoesNotExist:
            if not failure_return_none:
                raise  # Re-raise the exception
    else:
        current_site = get_current_site()
        if current_site:
            if current_site.id == settings.SITE_ID:
                if not failure_return_none:
                    raise NotImplementedError(
                        'get_current_organization: Cannot get organization of main site. Please use '
                        '`is_request_for_new_amc_site()` first'
                    )
            else:
                try:
                    if settings.FEATURES.get('TAHOE_ENABLE_MULTI_ORGS_PER_SITE', False):
                        if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
                            raise ImproperlyConfigured(
                                'TAHOE_ENABLE_MULTI_ORGS_PER_SITE and '
                                'APPSEMBLER_MULTI_TENANT_EMAILS are incompatible as '
                                'we are not able to determine the exact Org when more than one '
                                'is associated with a Site.')
                        current_org = current_site.organizations.first()
                        if not current_org:
                            raise Organization.DoesNotExist(
                                'TAHOE_ENABLE_MULTI_ORGS_PER_SITE: Could not find current '
                                'organization for site `{}`'.format(repr(current_site))
                            )
                    else:
                        current_org = current_site.organizations.get()
                except (Organization.DoesNotExist, ImproperlyConfigured):
                    if not failure_return_none:
                        raise  # Re-raise the exception
        else:
            if not failure_return_none:
                raise Exception('get_current_organization: Cannot get current site.')

    return current_org


@beeline.traced(name="is_request_for_new_amc_site")
def is_request_for_new_amc_site(request):
    """
    Check if request is being made for a new AMC signup.

    This helper returns True only for newly created site but not for AMC invited admin.
    """
    if not request or not request.method == 'POST':
        # Handle all no-request contexts and non-registration requests gracefully.
        return False

    is_for_admin = is_request_for_amc_admin(request)
    invitation_organization_name = request.POST.get('organization')
    return is_for_admin and not invitation_organization_name


@beeline.traced(name="get_customer_files_storage")
def get_customer_files_storage():
    kwargs = {}
    # Passing these settings to the FileSystemStorage causes an exception
    # TODO: Use settings instead of hardcoded in Python
    if not settings.DEBUG:
        kwargs = {
            'location': 'customer_files',
            'file_overwrite': False
        }

    return get_storage_class()(**kwargs)


@beeline.traced(name="get_initial_sass_variables")
def get_initial_sass_variables():
    """
    This method loads the SASS variables file from the currently active theme. It is used as a default value
    for the sass_variables field on new Microsite objects.
    """
    values = get_branding_values_from_file()
    labels = get_branding_labels_from_file()
    return [(val[0], (val[1], lab[1])) for val, lab in zip(values, labels)]


@beeline.traced(name="get_branding_values_from_file")
def get_branding_values_from_file():
    from openedx.core.djangoapps.theming.helpers import get_theme_base_dir, Theme

    if not settings.ENABLE_COMPREHENSIVE_THEMING:
        return {}

    try:
        default_site = Site.objects.get(id=settings.SITE_ID)
    except Site.DoesNotExist:
        # Empty values dictionary if the database isn't initialized yet.
        # This unblocks migrations and other cases before having a default site.
        return {}

    site_theme = SiteTheme(site=default_site, theme_dir_name=settings.DEFAULT_SITE_THEME)
    theme = Theme(
        name=site_theme.theme_dir_name,
        theme_dir_name=site_theme.theme_dir_name,
        themes_base_dir=get_theme_base_dir(site_theme.theme_dir_name),
        project_root=settings.PROJECT_ROOT,
    )
    if theme:
        sass_var_file = os.path.join(theme.customer_specific_path, 'static',
                                     'sass', 'base', '_branding-basics.scss')
        with open(sass_var_file, 'r') as f:
            contents = f.read()
            values = sass_to_dict(contents)
    else:
        values = {}
    return values


@beeline.traced(name="get_branding_labels_from_file")
def get_branding_labels_from_file(custom_branding=None):
    if not settings.ENABLE_COMPREHENSIVE_THEMING:
        return []

    css_output = compile_sass('_brand.scss', custom_branding)
    css_rules = cssutils.parseString(css_output, validate=False).cssRules
    labels = []
    for rule in css_rules:
        # we don't want comments in the final output
        if rule.typeString == "COMMENT":
            continue
        var_name = rule.selectorText.replace('.', '$')
        value = rule.style.content
        labels.append((var_name, value))
    return labels


@beeline.traced(name="compile_sass")
def compile_sass(sass_file, custom_branding=None):
    from openedx.core.djangoapps.theming.helpers import get_theme_base_dir, Theme
    try:
        default_site = Site.objects.get(id=settings.SITE_ID)
    except Site.DoesNotExist:
        # Empty CSS output if the database isn't initialized yet.
        # This unblocks migrations and other cases before having a default site.
        return ''

    site_theme = SiteTheme(site=default_site, theme_dir_name=settings.DEFAULT_SITE_THEME)
    theme = Theme(
        name=site_theme.theme_dir_name,
        theme_dir_name=site_theme.theme_dir_name,
        themes_base_dir=get_theme_base_dir(site_theme.theme_dir_name),
        project_root=settings.PROJECT_ROOT,
    )
    sass_var_file = os.path.join(theme.path, 'static', 'sass', sass_file)
    customer_specific_includes = os.path.join(theme.customer_specific_path, 'static', 'sass')
    importers = None
    if custom_branding:
        importers = [(0, custom_branding)]
    css_output = sass.compile(
        filename=sass_var_file,
        include_paths=[customer_specific_includes],
        importers=importers
    )
    return css_output


def sass_to_dict(sass_input):
    sass_vars = []
    lines = (line for line in sass_input.splitlines() if line and not line.startswith('//'))
    for line in lines:
        key, val = line.split(':')
        val = val.split('//')[0]
        val = val.strip().replace(";", "")
        sass_vars.append((key, val))
    return sass_vars


@beeline.traced(name="bootstrap_site")
def bootstrap_site(site, org_data=None, username=None):
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
    organization_slug = org_data.get('name')
    beeline.add_context_field("org_data", org_data)
    beeline.add_context_field("username", username)
    # don't use create because we need to call save() to set some values automatically
    site_config = SiteConfiguration(site=site, enabled=True)
    site_config.save()
    site.configuration_id = site_config.id
    beeline.add_context_field("site_config_id", site_config.id)
    # temp workarounds while old staging is still up and running
    if organization_slug:
        organization_data = org_api.add_organization({
            'name': organization_slug,
            'short_name': organization_slug,
            'edx_uuid': org_data.get('edx_uuid')
        })
        organization = org_models.Organization.objects.get(id=organization_data.get('id'))
        create_tahoe_site_by_link(organization=organization, site=site)
        site_config.site_values['course_org_filter'] = organization_slug
        site_config.save()
    else:
        organization = {}
    if username:
        user = User.objects.get(username=username)
        org_models.UserOrganizationMapping.objects.create(user=user, organization=organization, is_amc_admin=True)
    else:
        user = {}
    return organization, site, user


@beeline.traced(name="delete_site")
def delete_site(site):
    site.configuration.delete()
    site.themes.all().delete()

    site.delete()


@beeline.traced(name="add_course_creator_role")
def add_course_creator_role(user):
    """
    Allow users registered from AMC to create courses.

    This will fail in when running tests from within the AMC because the CMS migrations
    don't run during tests. Patch this function to avoid such errors.

    TODO: RED-2853 Remove this helper when AMC is removed
          This helper is being replaced by `update_course_creator_role_for_cms` which has unit tests.
    """
    from cms.djangoapps.course_creators.models import CourseCreator  # Fix LMS->CMS imports.
    from student.roles import CourseAccessRole, CourseCreatorRole  # Avoid circular import.
    CourseCreator.objects.update_or_create(user=user, defaults={'state': CourseCreator.GRANTED})
    CourseAccessRole.objects.create(user=user, role=CourseCreatorRole.ROLE, course_id=None, org='')


@beeline.traced(name="migrate_page_element")
def migrate_page_element(element):
    """
    Translate the `content` in the page element, apply the same for all children elements.
    """
    if not isinstance(element, dict):
        print('DEBUG:', element)
        raise Exception('An element should be a dict')

    if 'options' not in element:
        print('DEBUG:', element)
        raise Exception('Unknown element type')

    options = element['options']

    if 'content' in options or 'text-content' in options:
        if 'content' in options and 'text-content' in options:
            print('DEBUG:', options)
            raise Exception(
                'Both `content` and `text-content` are there, but which one to translate?'
            )

        if 'content' in options and not isinstance(options['content'], dict):
            options['content'] = {
                'en': options['content']
            }

        if 'text-content' in options and not isinstance(options['text-content'], dict):
            options['text-content'] = {
                'en': options['text-content']
            }

    for _column_name, children in element.get('children', {}).items():
        for child_element in children:
            migrate_page_element(child_element)


def to_new_page_elements(page_elements):
    """
    Migrate the page elements of a site.
    """
    for page_id, page_obj in page_elements.items():
        if isinstance(page_obj, str):
            continue  # Skip pages like `"course-card": "course-tile-01"`

        for element in page_obj.get('content', []):
            migrate_page_element(element)


def get_initial_page_elements():
    """
    Get the initial page elements, with i18n support.
    """
    initial_elements = _get_initial_page_elements()
    to_new_page_elements(initial_elements)
    return initial_elements


def _get_initial_page_elements():
    """
    Get the initial page elements, without i18n support.
    """
    # pylint: disable=line-too-long
    return {
        "embargo": {
            "content": []
        },
        "index": {
            "content": [
                {
                    "element-type": "layout-33:66",
                    "element-path": "page-builder/layouts/_two-col-33-66.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-100",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-75",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--72px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#0090c1",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Welcome to your Tahoe trial LMS site!"
                                    },
                                    "font-family": "font--primary--bold",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--20px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#323232",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Imagine how your courses might look like in your own Tahoe site"
                                    },
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "cta-button",
                                "element-path": "page-builder/elements/_cta-button.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "bg-color": "#0090c1",
                                    "border-color": "#0090c1",
                                    "margin-right": "marg-r-0",
                                    "border-width": "border-width--none",
                                    "margin-bottom": "marg-b-0",
                                    "text-color": "#fff",
                                    "margin-top": "marg-t-30",
                                    "padding-right": "padd-r-30",
                                    "margin-left": "marg-l-0",
                                    "url": "/login",
                                    "padding-bottom": "padd-b-15",
                                    "text-content": {
                                        "en": "Log in to start!"
                                    },
                                    "padding-top": "padd-t-15",
                                    "font-family": "font--primary--regular",
                                    "padding-left": "padd-l-30"
                                }
                            }
                        ],
                        "column-2": [
                            {
                                "element-type": "image-graphic",
                                "element-path": "page-builder/elements/_image-graphic.html",
                                "options": {
                                    "margin-left": "marg-l-auto",
                                    "image-alt-text": {
                                        "en": "Grow with Tahoe!"
                                    },
                                    "margin-bottom": "marg-b-0",
                                    "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/Tahoe-Figures-768x432.png",
                                    "margin-top": "marg-t-0",
                                    "margin-right": "marg-r-auto",
                                    "link-url": "",
                                    "image-width": "set-width--80percent"
                                }
                            }
                        ]
                    }
                },
                {
                    "element-type": "layout-33:66",
                    "element-path": "page-builder/layouts/_two-col-33-66.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#EFEFEF",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-50",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-30",
                                    "text-color": "#0090c1",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Appsembler sample course"
                                    },
                                    "font-family": "font--primary--bold",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--32px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-30",
                                    "text-color": "#0e0e0e",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Featured course"
                                    },
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--16px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#323232",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Learn about Appsembler, Tahoe and our hands-on Virtual Labs tool and get some tips and insights on how we built this course!"
                                    },
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "cta-button",
                                "element-path": "page-builder/elements/_cta-button.html",
                                "options": {
                                    "font-size": "font-size--16px",
                                    "bg-color": "rgba(255,255,255,0)",
                                    "border-color": "#0090c1",
                                    "margin-right": "marg-r-0",
                                    "border-width": "border-width--2px",
                                    "margin-bottom": "marg-b-0",
                                    "text-color": "#0090c1",
                                    "margin-top": "marg-t-30",
                                    "padding-right": "padd-r-30",
                                    "margin-left": "marg-l-0",
                                    "url": "/login",
                                    "padding-bottom": "padd-b-15",
                                    "text-content": {
                                        "en": "Start the course!"
                                    },
                                    "padding-top": "padd-t-15",
                                    "font-family": "font--primary--regular",
                                    "padding-left": "padd-l-30"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--12px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "rgba(14,14,14,0.6)",
                                    "margin-top": "marg-t-15",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "First you need to log in with the account you created during trial signup to interact with this Trial site. Once logged in, take our Appsembler sample course to learn more."
                                    },
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": [
                            {
                                "element-type": "layout-1:1:1",
                                "element-path": "page-builder/layouts/_three-col.html",
                                "options": {
                                    "layout-bg-image": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/lp--bg-blob_8Uo19jE.png",
                                    "bg-color": "rgba(255,255,255,0)",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-0",
                                    "layout-bg-image-size": "bg-img-size--contain",
                                    "text-color": "#000",
                                    "margin-top": "marg-t-0",
                                    "padding-right": "padd-r-0",
                                    "margin-left": "marg-l-0",
                                    "padding-bottom": "padd-b-50",
                                    "align-content": "align-content-center",
                                    "text-alignment": "text-align--left",
                                    "padding-top": "padd-t-50",
                                    "padding-left": "padd-l-0"
                                },
                                "children": {
                                    "column-1": [],
                                    "column-3": [],
                                    "column-2": [
                                        {
                                            "element-type": "courses-listing",
                                            "element-path": "page-builder/elements/_courses-listing.html",
                                            "options": {
                                                "tile-type": "course-tile-01",
                                                "num-of-courses": "4",
                                                "text-alignment": "text-align--left"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-75",
                        "align-content": "align-content-top",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-75",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "layout-50:50",
                                "element-path": "page-builder/layouts/_two-col-50-50.html",
                                "options": {
                                    "layout-bg-image": "",
                                    "bg-color": "#fff",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-0",
                                    "layout-bg-image-size": "bg-img-size--cover",
                                    "text-color": "#000",
                                    "margin-top": "marg-t-0",
                                    "padding-right": "padd-r-0",
                                    "margin-left": "marg-l-0",
                                    "padding-bottom": "padd-b-20",
                                    "align-content": "align-content-top",
                                    "text-alignment": "text-align--left",
                                    "padding-top": "padd-t-20",
                                    "padding-left": "padd-l-0"
                                },
                                "children": {
                                    "column-1": [
                                        {
                                            "element-type": "image-graphic",
                                            "element-path": "page-builder/elements/_image-graphic.html",
                                            "options": {
                                                "margin-left": "marg-l-auto",
                                                "image-alt-text": {
                                                    "en": "Access the LMS"
                                                },
                                                "margin-bottom": "marg-b-30",
                                                "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/access-the-lms.png",
                                                "margin-top": "marg-t-0",
                                                "margin-right": "marg-r-auto",
                                                "link-url": "",
                                                "image-width": "set-width--30percent"
                                            }
                                        },
                                        {
                                            "element-type": "heading",
                                            "element-path": "page-builder/elements/_heading.html",
                                            "options": {
                                                "font-size": "font-size--24px",
                                                "margin-right": "marg-r-0",
                                                "margin-bottom": "marg-b-20",
                                                "text-color": "#0090c1",
                                                "margin-top": "marg-t-0",
                                                "margin-left": "marg-l-0",
                                                "text-content": {
                                                    "en": "Access the LMS"
                                                },
                                                "font-family": "font--primary--bold",
                                                "text-alignment": "text-align--center"
                                            }
                                        },
                                        {
                                            "element-type": "paragraph-text",
                                            "element-path": "page-builder/elements/_paragraph.html",
                                            "options": {
                                                "font-size": "font-size--14px",
                                                "margin-right": "marg-r-20",
                                                "margin-bottom": "marg-b-5",
                                                "text-color": "#323232",
                                                "margin-top": "marg-t-5",
                                                "margin-left": "marg-l-20",
                                                "text-content": {
                                                    "en": "This is where your learners can take their training courses and your instructors can handle learner management."
                                                },
                                                "font-family": "font--primary--regular",
                                                "text-alignment": "text-align--center"
                                            }
                                        }
                                    ],
                                    "column-2": [
                                        {
                                            "element-type": "image-graphic",
                                            "element-path": "page-builder/elements/_image-graphic.html",
                                            "options": {
                                                "margin-left": "marg-l-auto",
                                                "image-alt-text": {
                                                    "en": "Get to know Studio"
                                                },
                                                "margin-bottom": "marg-b-30",
                                                "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/get-to-know-studio.png",
                                                "margin-top": "marg-t-0",
                                                "margin-right": "marg-r-auto",
                                                "link-url": "",
                                                "image-width": "set-width--30percent"
                                            }
                                        },
                                        {
                                            "element-type": "heading",
                                            "element-path": "page-builder/elements/_heading.html",
                                            "options": {
                                                "font-size": "font-size--24px",
                                                "margin-right": "marg-r-0",
                                                "margin-bottom": "marg-b-20",
                                                "text-color": "#0090c1",
                                                "margin-top": "marg-t-0",
                                                "margin-left": "marg-l-0",
                                                "text-content": {
                                                    "en": "Get to know Studio"
                                                },
                                                "font-family": "font--primary--bold",
                                                "text-alignment": "text-align--center"
                                            }
                                        },
                                        {
                                            "element-type": "paragraph-text",
                                            "element-path": "page-builder/elements/_paragraph.html",
                                            "options": {
                                                "font-size": "font-size--14px",
                                                "margin-right": "marg-r-20",
                                                "margin-bottom": "marg-b-5",
                                                "text-color": "#323232",
                                                "margin-top": "marg-t-5",
                                                "margin-left": "marg-l-20",
                                                "text-content": {
                                                    "en": "You'll get to see how the Sample course is built and create your own courses."
                                                },
                                                "font-family": "font--primary--regular",
                                                "text-alignment": "text-align--center"
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                        "column-2": [
                            {
                                "element-type": "layout-50:50",
                                "element-path": "page-builder/layouts/_two-col-50-50.html",
                                "options": {
                                    "layout-bg-image": "",
                                    "bg-color": "#fff",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-0",
                                    "layout-bg-image-size": "bg-img-size--cover",
                                    "text-color": "#000",
                                    "margin-top": "marg-t-0",
                                    "padding-right": "padd-r-0",
                                    "margin-left": "marg-l-0",
                                    "padding-bottom": "padd-b-20",
                                    "align-content": "align-content-top",
                                    "text-alignment": "text-align--left",
                                    "padding-top": "padd-t-20",
                                    "padding-left": "padd-l-0"
                                },
                                "children": {
                                    "column-1": [
                                        {
                                            "element-type": "image-graphic",
                                            "element-path": "page-builder/elements/_image-graphic.html",
                                            "options": {
                                                "margin-left": "marg-l-auto",
                                                "image-alt-text": {
                                                    "en": "Manage your site"
                                                },
                                                "margin-bottom": "marg-b-30",
                                                "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/manage-your-site.png",
                                                "margin-top": "marg-t-0",
                                                "margin-right": "marg-r-auto",
                                                "link-url": "",
                                                "image-width": "set-width--30percent"
                                            }
                                        },
                                        {
                                            "element-type": "heading",
                                            "element-path": "page-builder/elements/_heading.html",
                                            "options": {
                                                "font-size": "font-size--24px",
                                                "margin-right": "marg-r-0",
                                                "margin-bottom": "marg-b-20",
                                                "text-color": "#0090c1",
                                                "margin-top": "marg-t-0",
                                                "margin-left": "marg-l-0",
                                                "text-content": {
                                                    "en": "Manage your site"
                                                },
                                                "font-family": "font--primary--bold",
                                                "text-alignment": "text-align--center"
                                            }
                                        },
                                        {
                                            "element-type": "paragraph-text",
                                            "element-path": "page-builder/elements/_paragraph.html",
                                            "options": {
                                                "font-size": "font-size--14px",
                                                "margin-right": "marg-r-20",
                                                "margin-bottom": "marg-b-5",
                                                "text-color": "#323232",
                                                "margin-top": "marg-t-5",
                                                "margin-left": "marg-l-20",
                                                "text-content": {
                                                    "en": "In the Management Console, you'll define your site's look and feel and manage site-wide content (e.g. certificates, SSO, custom domain)."
                                                },
                                                "font-family": "font--primary--regular",
                                                "text-alignment": "text-align--center"
                                            }
                                        }
                                    ],
                                    "column-2": [
                                        {
                                            "element-type": "image-graphic",
                                            "element-path": "page-builder/elements/_image-graphic.html",
                                            "options": {
                                                "margin-left": "marg-l-auto",
                                                "image-alt-text": {
                                                    "en": "Get reports"
                                                },
                                                "margin-bottom": "marg-b-30",
                                                "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/get-reports.png",
                                                "margin-top": "marg-t-0",
                                                "margin-right": "marg-r-auto",
                                                "link-url": "",
                                                "image-width": "set-width--30percent"
                                            }
                                        },
                                        {
                                            "element-type": "heading",
                                            "element-path": "page-builder/elements/_heading.html",
                                            "options": {
                                                "font-size": "font-size--24px",
                                                "margin-right": "marg-r-0",
                                                "margin-bottom": "marg-b-20",
                                                "text-color": "#0090c1",
                                                "margin-top": "marg-t-0",
                                                "margin-left": "marg-l-0",
                                                "text-content": {
                                                    "en": "Get reports"
                                                },
                                                "font-family": "font--primary--bold",
                                                "text-alignment": "text-align--center"
                                            }
                                        },
                                        {
                                            "element-type": "paragraph-text",
                                            "element-path": "page-builder/elements/_paragraph.html",
                                            "options": {
                                                "font-size": "font-size--14px",
                                                "margin-right": "marg-r-20",
                                                "margin-bottom": "marg-b-5",
                                                "text-color": "#323232",
                                                "margin-top": "marg-t-5",
                                                "margin-left": "marg-l-20",
                                                "text-content": {
                                                    "en": "Understand how your learners are doing in your courses."
                                                },
                                                "font-family": "font--primary--regular",
                                                "text-alignment": "text-align--center"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                {
                    "element-type": "layout-33:66",
                    "element-path": "page-builder/layouts/_two-col-33-66.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#EEEEEE",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-200",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-75",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "image-graphic",
                                "element-path": "page-builder/elements/_image-graphic.html",
                                "options": {
                                    "margin-left": "marg-l-auto",
                                    "image-alt-text": {
                                        "en": "Appsembler Support"
                                    },
                                    "margin-bottom": "marg-b-0",
                                    "image-file": "https://s3.amazonaws.com/staging-tahoe-bucket/customer_files/support-graphic.svg",
                                    "margin-top": "marg-t-0",
                                    "margin-right": "marg-r-50",
                                    "link-url": "",
                                    "image-width": "set-width--100percent"
                                }
                            }
                        ],
                        "column-2": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-30",
                                    "text-color": "#0090c1",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "We've got you covered."
                                    },
                                    "font-family": "font--primary--bold",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--32px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-30",
                                    "text-color": "#0e0e0e",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": {
                                        "en": "Wondering how to start creating courses?"
                                    },
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": {
                                        "en": "<ul><li>The <a href='https://academy.appsembler.com/' target='_blank'>Appsembler Academy</a> is the home of Appsembler's own courses, including <a href='https://academy.appsembler.com/courses/course-v1:appsembleracademy+OX11+Perpetual/about' target='_blank'>Creating Your First Course</a></li><li>Our <a href='https://www.youtube.com/channel/UCINXF1QU7s1D4Tvp0AnWPKA' target='_blank'>YouTube channel</a> has plenty of videos and webinars for you to explore</li><li>Our <a href='https://help.appsembler.com/' target='_blank'>knowledge base</a> is where we keep all of our articles on how to accomplish specific tasks with your Tahoe site</li></ul><p>If you get stuck or have any questions, just contact us using the chat widget down in the bottom right. We're online from 5am to 5pm Eastern US Time, Monday to Friday, and we're happy to help!</p>"
                                    },
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "about": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "course-about": {
            "content": [
                {
                    "element-type": "course-about-template",
                    "element-path": "design-templates/pages/course-about/_course-about-01.html",
                    "options": {
                        "courseware-button-view-courseware-text": "View Courseware",
                        "courseware-button-enroll-text": "Enroll in",
                        "courseware-button-in-cart-text": "Course is in your cart.",
                        "view-in-studio-button-text": "View About Page in studio",
                        "courseware-button-enrollment-closed-text": "Enrollment is Closed",
                        "courseware-button-add-to-cart-text": "Add to Cart / Price:",
                        "courseware-button-invitation-only-text": "Enrollment in this course is by invitation only",
                        "courseware-button-course-full-text": "Course is full",
                        "courseware-button-already-enrolled-text": "You are enrolled in this course"
                    }
                }
            ]
        },
        "jobs": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "help": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "copyright": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "privacy": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "course-card": "course-tile-01",
        "faq": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "blog": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "courses": {
            "content": [
                {
                    "element-type": "course-catalogue-template",
                    "element-path": "design-templates/pages/course-catalogue/_course-catalogue-01.html",
                    "options": {
                        "discovery-facet-option": "facet_option-01",
                        "course-card": "course-tile-01",
                        "search-enabled": True,
                        "discovery-facet": "facet-01"
                    }
                }
            ]
        },
        "contact": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "tos": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "press": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "news": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "donate": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        },
        "honor": {
            "content": [
                {
                    "element-type": "layout-50:50",
                    "element-path": "page-builder/layouts/_two-col-50-50.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#34495e",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-50",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-200",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "heading",
                                "element-path": "page-builder/elements/_heading.html",
                                "options": {
                                    "font-size": "font-size--48px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-20",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-0",
                                    "margin-left": "marg-l-0",
                                    "text-content": "This is an example title of the static page",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            },
                            {
                                "element-type": "paragraph-text",
                                "element-path": "page-builder/elements/_paragraph.html",
                                "options": {
                                    "font-size": "font-size--18px",
                                    "margin-right": "marg-r-0",
                                    "margin-bottom": "marg-b-5",
                                    "text-color": "#ffffff",
                                    "margin-top": "marg-t-5",
                                    "margin-left": "marg-l-0",
                                    "text-content": "Vivamus scelerisque odio ut lectus luctus, eget viverra leo aliquet.",
                                    "font-family": "font--primary--regular",
                                    "text-alignment": "text-align--left"
                                }
                            }
                        ],
                        "column-2": []
                    }
                },
                {
                    "element-type": "layout-single-col",
                    "element-path": "page-builder/layouts/_single-col.html",
                    "options": {
                        "layout-bg-image": "",
                        "bg-color": "#fff",
                        "margin-right": "marg-r-0",
                        "margin-bottom": "marg-b-0",
                        "layout-bg-image-size": "bg-img-size--cover",
                        "text-color": "#000",
                        "margin-top": "marg-t-0",
                        "padding-right": "padd-r-0",
                        "margin-left": "marg-l-0",
                        "padding-bottom": "padd-b-20",
                        "align-content": "align-content-center",
                        "text-alignment": "text-align--left",
                        "padding-top": "padd-t-20",
                        "padding-left": "padd-l-0"
                    },
                    "children": {
                        "column-1": [
                            {
                                "element-type": "content-block",
                                "element-path": "page-builder/elements/_content-block.html",
                                "options": {
                                    "content": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <a href=\"#\">Mauris libero nulla</a>, sagittis at erat non, commodo porta nunc. Donec ultrices erat vel vehicula posuere. Morbi a justo metus. Ut et libero congue, interdum diam sit amet, scelerisque massa. Sed non purus mi. Fusce posuere vel ante eu tempus.<em> Integer interdum libero libero, sit amet fermentum nisl pretium ac. In suscipit, elit eget vulputate bibendum, arcu libero </em><em><strong>tristique</strong></em><em> diam, ut fringilla augue est in neque.</em> Suspendisse consequat ex non lacinia sodales.In feugiat eu erat non interdum. <del>Donec nec accumsan augue.</del> Sed consequat quis mauris ut interdum. Aliquam porttitor risus egestas, maximus quam a, cursus erat. Donec in sem ligula. Sed non convallis dui. Phasellus scelerisque maximus vestibulum.</p>\n<p><br></p>\n<h1>This is an H1 (large) heading</h1>\n<p>Fusce nunc est, euismod sit amet vehicula non, facilisis eu purus. Curabitur cursus et neque nec fringilla. Phasellus aliquam pulvinar risus. Praesent magna sem, consequat ut quam at, euismod maximus ipsum. Vestibulum porttitor blandit ultrices. <strong>Nam tempus hendrerit</strong> ipsum vitae elementum. Suspendisse sit amet eleifend tellus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean nec aliquam leo.Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh. Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris. Nullam tristique semper condimentum. Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna. Suspendisse dignissim dui quis dolor fringilla porttitor. Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.Pellentesque sit amet pellentesque felis.</p>\n<p><br></p>\n<h2>This is an H2 (medium) heading</h2>\n<p>Phasellus ex massa, hendrerit porta hendrerit a, pretium et justo. <ins>Vivamus eget dui sed justo consequat malesuada. Integer a commodo augue.</ins> Morbi rutrum suscipit efficitur. Vivamus ac libero ullamcorper, rhoncus nulla at, accumsan tellus. In hac habitasse platea dictumst. Donec maximus ex a faucibus commodo. In vel eros non diam pellentesque maximus. Curabitur fermentum accumsan lectus, ut aliquam ipsum pulvinar quis. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;Nam convallis egestas consectetur. Ut ac eleifend enim, a efficitur magna. Sed cursus ornare finibus. Mauris quis tincidunt justo. Cras efficitur, enim non pharetra ultrices, eros augue eleifend nisl, at congue elit leo quis arcu. Sed luctus, nibh vitae efficitur maximus, turpis ante porta diam, facilisis ultrices dui sem sed libero. Nulla pulvinar nisi eget cursus eleifend. Aliquam erat volutpat. Integer tortor nulla, auctor vitae vestibulum ut, sagittis sed velit. Integer a luctus arcu. Nam congue et elit sit amet porta. Cras euismod ipsum massa, quis elementum ligula lobortis quis. Mauris eu augue efficitur, feugiat augue non, aliquam ligula.Nulla a orci a felis mollis scelerisque. Pellentesque neque velit, faucibus nec mi eu, commodo tincidunt risus.</p>\n<p><br></p>\n<h3>This is an H3 (small) heading</h3>\n<p>Sed tempus justo leo, non sollicitudin mi eleifend a. Curabitur sed diam pulvinar, dictum nisl ut, blandit metus. Maecenas non sem quis ligula commodo egestas. Integer malesuada eleifend est, in commodo eros fermentum sed. Maecenas commodo nibh quis porttitor vehicula. Aenean blandit rutrum dolor, non ullamcorper est aliquam ac.Etiam interdum semper tempor. Phasellus condimentum massa eu libero sagittis cursus. Sed at lorem vel nulla elementum fringilla nec at eros. Aenean facilisis scelerisque tortor, non malesuada arcu scelerisque a. Ut est ante, iaculis at ultricies non, molestie placerat leo. Cras ullamcorper pellentesque erat in blandit. Nunc tortor ligula, fringilla ac risus quis, venenatis iaculis quam. Aliquam eget ex vitae ligula imperdiet finibus. Nullam ex metus, placerat ac arcu non, imperdiet consequat tortor. Donec varius elementum odio et rutrum. Sed in aliquam eros, sed sagittis erat. Vivamus tristique congue dictum. Proin tincidunt quis neque eget aliquam. Morbi sollicitudin orci lectus, a vulputate turpis porta a. Fusce facilisis ullamcorper dui in consequat.</p>\n<p><br></p>\n<h3>Code block follows</h3>\n<pre><code>Sed vitae convallis sapien, mollis fermentum ex.Curabitur rhoncus leo accumsan eros scelerisque, eget rhoncus augue porttitor. Praesent pretium mattis nibh, sit amet euismod nulla suscipit nec. Proin vehicula felis sit amet libero tempor, faucibus ultrices leo laoreet. Phasellus ultricies sapien urna, eget fringilla turpis rutrum vel. Donec nec nisl ultricies, lacinia diam in, finibus elit. Maecenas et felis eu lectus ultricies vestibulum. Aliquam accumsan efficitur lectus ut consequat. Sed quis aliquet justo, ut convallis eros.Vivamus vestibulum quam dictum orci aliquam, eget tincidunt est tincidunt. Curabitur pretium ut elit eget aliquet. Sed rhoncus metus sapien, eget malesuada ex dictum eu. Quisque auctor magna nibh, vel sollicitudin dui cursus sit amet.</code></pre>\n<p>In laoreet faucibus lorem vel fringilla. Sed et dolor sem. Proin velit augue, condimentum in enim sed, finibus tincidunt purus. Maecenas efficitur, lacus finibus vulputate luctus, urna eros iaculis lacus, a cursus lacus metus sit amet lacus. Maecenas porttitor imperdiet magna, et scelerisque nunc ornare nec. Integer consequat hendrerit neque, sed condimentum velit commodo a.</p>\n<p><br></p>\n<h3>Unordered list:</h3>\n<p>Praesent ultricies commodo arcu, at vulputate metus rutrum ut.Etiam vel ante vel nulla pellentesque aliquam sed at erat. In faucibus ac leo a dignissim. Donec augue lorem, sagittis sed tempus et, auctor vitae risus:</p>\n<ul>\n  <li>Fusce vel bibendum felis.</li>\n  <li>Phasellus vitae diam felis. Nulla rhoncus felis sit amet fringilla tincidunt. Pellentesque vestibulum, est non congue hendrerit, elit leo bibendum mauris, a malesuada quam massa ut lectus.</li>\n  <li>Vestibulum nec ornare neque.</li>\n  <li>Nunc mattis ex in vestibulum dapibus.</li>\n  <li>Quisque cursus lacus dui, consequat viverra purus lobortis ac. In hac habitasse platea dictumst.</li>\n</ul>\n<h3><br></h3>\n<h3>Ordered list:</h3>\n<p>Mauris sollicitudin ligula vitae erat mollis, a hendrerit mi molestie. Proin sit amet diam quis dolor ornare lacinia eu ut dui. In vitae congue diam. Aenean pharetra feugiat nulla, in ultrices nisl venenatis non. Donec nulla turpis, commodo eget pretium non, auctor vestibulum nibh:</p>\n<ol>\n  <li>Donec sit amet sodales augue. Ut et odio at magna tempus interdum quis ut mauris.</li>\n  <li>Nullam tristique semper condimentum.</li>\n  <li>Sed sollicitudin lacus at felis vehicula bibendum. Nunc pharetra tincidunt urna.</li>\n  <li>Suspendisse dignissim dui quis dolor fringilla porttitor.</li>\n  <li>Morbi pellentesque eros quis lacus tristique maximus. Suspendisse laoreet sagittis ultrices.</li>\n</ol>",
                                    "margin-top": "marg-t-30",
                                    "margin-bottom": "marg-b-100",
                                    "margin-left": "marg-l-0",
                                    "margin-right": "marg-r-0"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
