# pylint: disable=bad-continuation
"""
Certificate HTML webview.
"""


import logging
from datetime import datetime
from uuid import uuid4

import six
import pytz

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.template import RequestContext
from django.utils import translation
from django.utils.encoding import smart_str
from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.badges.events.course_complete import get_completion_badge
from lms.djangoapps.badges.utils import badges_enabled
from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.edxmako.template import Template
from lms.djangoapps.certificates.api import (
    emit_certificate_event,
    get_active_web_certificate,
    get_certificate_footer_context,
    get_certificate_header_context,
    get_certificate_template,
    get_certificate_url
)
from lms.djangoapps.certificates.models import (
    CertificateGenerationCourseSetting,
    CertificateHtmlViewConfiguration,
    CertificateSocialNetworks,
    CertificateStatuses,
    GeneratedCertificate
)
from lms.djangoapps.certificates.permissions import PREVIEW_CERTIFICATES
from lms.djangoapps.courseware.courses import get_course_by_id
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.certificates.api import certificates_viewable_for_course, display_date_for_certificate
from openedx.core.djangoapps.lang_pref.api import get_closest_released_language
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.courses import course_image_url
from common.djangoapps.student.models import LinkedInAddToProfileConfiguration
from common.djangoapps.util import organizations_helpers as organization_api
from common.djangoapps.util.date_utils import strftime_localized
from common.djangoapps.util.views import handle_500

log = logging.getLogger(__name__)
_ = translation.ugettext


INVALID_CERTIFICATE_TEMPLATE_PATH = 'certificates/invalid.html'


def get_certificate_description(mode, certificate_type, platform_name):
    """
    :return certificate_type_description on the basis of current mode
    """
    certificate_type_description = None
    if mode == 'honor':
        # Translators:  This text describes the 'Honor' course certificate type.
        certificate_type_description = _(u"An {cert_type} certificate signifies that a "
                                         u"learner has agreed to abide by the honor code established by {platform_name} "
                                         u"and has completed all of the required tasks for this course under its "
                                         u"guidelines.").format(cert_type=certificate_type,
                                                                platform_name=platform_name)
    elif mode == 'verified':
        # Translators:  This text describes the 'ID Verified' course certificate type, which is a higher level of
        # verification offered by edX.  This type of verification is useful for professional education/certifications
        certificate_type_description = _(u"A {cert_type} certificate signifies that a "
                                         u"learner has agreed to abide by the honor code established by {platform_name} "
                                         u"and has completed all of the required tasks for this course under its "
                                         u"guidelines. A {cert_type} certificate also indicates that the "
                                         u"identity of the learner has been checked and "
                                         u"is valid.").format(cert_type=certificate_type,
                                                              platform_name=platform_name)
    elif mode == 'xseries':
        # Translators:  This text describes the 'XSeries' course certificate type.  An XSeries is a collection of
        # courses related to each other in a meaningful way, such as a specific topic or theme, or even an organization
        certificate_type_description = _(u"An {cert_type} certificate demonstrates a high level of "
                                         u"achievement in a program of study, and includes verification of "
                                         u"the student's identity.").format(cert_type=certificate_type)
    return certificate_type_description

def grade_percent_scaled(grade_percent, grade_cutoff):
    """
        EOL: Scale grade percent by grade cutoff. Grade between 1.0 - 7.0
    """
    if grade_percent == 0.:
        return 1.
    if grade_percent < grade_cutoff:
        return round(10. * (3. / grade_cutoff * grade_percent + 1.)) / 10.
    return round((3. / (1. - grade_cutoff) * grade_percent + (7. - (3. / (1. - grade_cutoff)))) * 10.) / 10.


def _update_certificate_context(context, course, user_certificate, platform_name):
    """
    Build up the certificate web view context using the provided values
    (Helper method to keep the view clean)
    """
    # Populate dynamic output values using the course/certificate data loaded above
    certificate_type = context.get('certificate_type')

    # Override the defaults with any mode-specific static values
    context['certificate_id_number'] = user_certificate.verify_uuid
    context['certificate_verify_url'] = u"{prefix}{uuid}{suffix}".format(
        prefix=context.get('certificate_verify_url_prefix'),
        uuid=user_certificate.verify_uuid,
        suffix=context.get('certificate_verify_url_suffix')
    )

    # Translators:  The format of the date includes the full name of the month
    date = display_date_for_certificate(course, user_certificate)
    context['certificate_date_issued'] = _(u'{month} {day}, {year}').format(
        month=strftime_localized(date, "%B"),
        day=date.day,
        year=date.year
    )

    # Translators:  This text represents the verification of the certificate
    context['document_meta_description'] = _(u'This is a valid {platform_name} certificate for {user_name}, '
                                             u'who participated in {partner_short_name} {course_number}').format(
        platform_name=platform_name,
        user_name=context['accomplishment_copy_name'],
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number']
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears in the browser title bar
    context['document_title'] = _(u"{partner_short_name} {course_number} Certificate | {platform_name}").format(
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number'],
        platform_name=platform_name
    )

    # Translators:  This text fragment appears after the student's name (displayed in a large font) on the certificate
    # screen.  The text describes the accomplishment represented by the certificate information displayed to the user
    context['accomplishment_copy_description_full'] = _(u"successfully completed, received a passing grade, and was "
                                                        u"awarded this {platform_name} {certificate_type} "
                                                        u"Certificate of Completion in ").format(
        platform_name=platform_name,
        certificate_type=context.get("certificate_type"))

    certificate_type_description = get_certificate_description(user_certificate.mode, certificate_type, platform_name)
    if certificate_type_description:
        context['certificate_type_description'] = certificate_type_description

    # EOL
    grade_cutoff = min(course.grade_cutoffs.values())  # Get the min value
    try:
        grade_percent = float(user_certificate.grade)
    except ValueError:
        grade_percent = 0.0
    context['eol_grade'] = grade_percent_scaled(grade_percent, grade_cutoff)
    context['eol_grade_percent'] = str(grade_percent)
    context['eol_grade_integer'] = str(int(grade_percent * 100))
    # EOL

    # Translators: This text describes the purpose (and therefore, value) of a course certificate
    context['certificate_info_description'] = _(u"{platform_name} acknowledges achievements through "
                                                u"certificates, which are awarded for course activities "
                                                u"that {platform_name} students complete.").format(
        platform_name=platform_name,
    )


def _update_context_with_basic_info(context, course_id, platform_name, configuration):
    """
    Updates context dictionary with basic info required before rendering simplest
    certificate templates.
    """
    context['platform_name'] = platform_name
    context['course_id'] = course_id

    # Update the view context with the default ConfigurationModel settings
    context.update(configuration.get('default', {}))

    # Translators:  'All rights reserved' is a legal term used in copyrighting to protect published content
    reserved = _("All rights reserved")
    context['copyright_text'] = u'&copy; {year} {platform_name}. {reserved}.'.format(
        year=datetime.now(pytz.timezone(settings.TIME_ZONE)).year,
        platform_name=platform_name,
        reserved=reserved
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears
    # in the browser title bar when a requested certificate is not found or recognized
    context['document_title'] = _("Invalid Certificate")

    context['company_tos_urltext'] = _("Terms of Service & Honor Code")

    # Translators: A 'Privacy Policy' is a legal document/statement describing a website's use of personal information
    context['company_privacy_urltext'] = _("Privacy Policy")

    # Translators: This line appears as a byline to a header image and describes the purpose of the page
    context['logo_subtitle'] = _("Certificate Validation")

    # Translators: Accomplishments describe the awards/certifications obtained by students on this platform
    context['accomplishment_copy_about'] = _(u'About {platform_name} Accomplishments').format(
        platform_name=platform_name
    )

    # Translators:  This line appears on the page just before the generation date for the certificate
    context['certificate_date_issued_title'] = _("Issued On:")

    # Translators:  The Certificate ID Number is an alphanumeric value unique to each individual certificate
    context['certificate_id_number_title'] = _('Certificate ID Number')

    context['certificate_info_title'] = _(u'About {platform_name} Certificates').format(
        platform_name=platform_name
    )

    context['certificate_verify_title'] = _(u"How {platform_name} Validates Student Certificates").format(
        platform_name=platform_name
    )

    # Translators:  This text describes the validation mechanism for a certificate file (known as GPG security)
    context['certificate_verify_description'] = _(u'Certificates issued by {platform_name} are signed by a gpg key so '
                                                  u'that they can be validated independently by anyone with the '
                                                  u'{platform_name} public key. For independent verification, '
                                                  u'{platform_name} uses what is called a '
                                                  u'"detached signature"&quot;".').format(platform_name=platform_name)

    context['certificate_verify_urltext'] = _("Validate this certificate for yourself")

    # Translators:  This text describes (at a high level) the mission and charter the edX platform and organization
    context['company_about_description'] = _(u"{platform_name} offers interactive online classes and MOOCs.").format(
        platform_name=platform_name)

    context['company_about_title'] = _(u"About {platform_name}").format(platform_name=platform_name)

    context['company_about_urltext'] = _(u"Learn more about {platform_name}").format(platform_name=platform_name)

    context['company_courselist_urltext'] = _(u"Learn with {platform_name}").format(platform_name=platform_name)

    context['company_careers_urltext'] = _(u"Work at {platform_name}").format(platform_name=platform_name)

    context['company_contact_urltext'] = _(u"Contact {platform_name}").format(platform_name=platform_name)

    # Translators:  This text appears near the top of the certficate and describes the guarantee provided by edX
    context['document_banner'] = _(u"{platform_name} acknowledges the following student accomplishment").format(
        platform_name=platform_name
    )


def _update_course_context(request, context, course, course_key, platform_name):
    """
    Updates context dictionary with course info.
    """
    context['full_course_image_url'] = request.build_absolute_uri(course_image_url(course))
    course_title_from_cert = context['certificate_data'].get('course_title', '')
    accomplishment_copy_course_name = course_title_from_cert if course_title_from_cert else course.display_name
    context['accomplishment_copy_course_name'] = accomplishment_copy_course_name
    course_number = course.display_coursenumber if course.display_coursenumber else course.number
    context['course_number'] = course_number
    if context['organization_long_name']:
        # Translators:  This text represents the description of course
        context['accomplishment_copy_course_description'] = _(u'a course of study offered by {partner_short_name}, '
                                                              'an online learning initiative of '
                                                              '{partner_long_name}.').format(
            partner_short_name=context['organization_short_name'],
            partner_long_name=context['organization_long_name'],
            platform_name=platform_name)
    else:
        # Translators:  This text represents the description of course
        context['accomplishment_copy_course_description'] = _('a course of study offered by '
                                                              '{partner_short_name}.').format(
            partner_short_name=context['organization_short_name'],
            platform_name=platform_name)


def _update_social_context(request, context, course, user, user_certificate, platform_name):
    """
    Updates context dictionary with info required for social sharing.
    """
    share_settings = configuration_helpers.get_value("SOCIAL_SHARING_SETTINGS", settings.SOCIAL_SHARING_SETTINGS)
    context['facebook_share_enabled'] = share_settings.get('CERTIFICATE_FACEBOOK', False)
    context['facebook_app_id'] = configuration_helpers.get_value("FACEBOOK_APP_ID", settings.FACEBOOK_APP_ID)
    context['facebook_share_text'] = share_settings.get(
        'CERTIFICATE_FACEBOOK_TEXT',
        _(u"I completed the {course_title} course on {platform_name}.").format(
            course_title=context['accomplishment_copy_course_name'],
            platform_name=platform_name
        )
    )
    context['twitter_share_enabled'] = share_settings.get('CERTIFICATE_TWITTER', False)
    context['twitter_share_text'] = share_settings.get(
        'CERTIFICATE_TWITTER_TEXT',
        _(u"I completed a course at {platform_name}. Take a look at my certificate.").format(
            platform_name=platform_name
        )
    )

    share_url = request.build_absolute_uri(get_certificate_url(course_id=course.id, uuid=user_certificate.verify_uuid))
    context['share_url'] = share_url
    twitter_url = ''
    if context.get('twitter_share_enabled', False):
        twitter_url = 'https://twitter.com/intent/tweet?text={twitter_share_text}&url={share_url}'.format(
            twitter_share_text=smart_str(context['twitter_share_text']),
            share_url=six.moves.urllib.parse.quote_plus(smart_str(share_url))
        )
    context['twitter_url'] = twitter_url
    context['linked_in_url'] = None
    # If enabled, show the LinkedIn "add to profile" button
    # Clicking this button sends the user to LinkedIn where they
    # can add the certificate information to their profile.
    linkedin_config = LinkedInAddToProfileConfiguration.current()
    if linkedin_config.is_enabled():
        context['linked_in_url'] = linkedin_config.add_to_profile_url(
            course.display_name, user_certificate.mode, smart_str(share_url), certificate=user_certificate
        )


def _update_context_with_user_info(context, user, user_certificate):
    """
    Updates context dictionary with user related info.
    """
    # user_fullname = user.profile.name
    context['username'] = user.username
    context['course_mode'] = user_certificate.mode
    context['accomplishment_user_id'] = user.id
    context['accomplishment_copy_name'] = user_certificate.name # EOL
    context['accomplishment_copy_username'] = user.username

    context['accomplishment_more_title'] = _(u"More Information About {user_name}'s Certificate:").format(
        user_name=user_certificate.name
    )
    # Translators: This line is displayed to a user who has completed a course and achieved a certification
    context['accomplishment_banner_opening'] = _(u"{fullname}, you earned a certificate!").format(
        fullname=user_certificate.name
    )

    # Translators: This line congratulates the user and instructs them to share their accomplishment on social networks
    context['accomplishment_banner_congrats'] = _("Congratulations! This page summarizes what "
                                                  "you accomplished. Show it off to family, friends, and colleagues "
                                                  "in your social and professional networks.")

    # Translators: This line leads the reader to understand more about the certificate that a student has been awarded
    context['accomplishment_copy_more_about'] = _(u"More about {fullname}'s accomplishment").format(
        fullname=user_certificate.name
    )


def _get_user_certificate(request, user, course_key, course, preview_mode=None):
    """
    Retrieves user's certificate from db. Creates one in case of preview mode.
    Returns None if there is no certificate generated for given user
    otherwise returns `GeneratedCertificate` instance.
    """
    user_certificate = None
    if preview_mode:
        # certificate is being previewed from studio
        if request.user.has_perm(PREVIEW_CERTIFICATES, course):
            if course.certificate_available_date and not course.self_paced:
                modified_date = course.certificate_available_date
            else:
                modified_date = datetime.now().date()
            user_certificate = GeneratedCertificate(
                mode=preview_mode,
                verify_uuid=six.text_type(uuid4().hex),
                modified_date=modified_date,
                created_date=datetime.now().date(),
            )
    elif certificates_viewable_for_course(course):
        # certificate is being viewed by learner or public
        try:
            user_certificate = GeneratedCertificate.eligible_certificates.get(
                user=user,
                course_id=course_key,
                status=CertificateStatuses.downloadable
            )
        except GeneratedCertificate.DoesNotExist:
            pass

    return user_certificate


def _track_certificate_events(request, context, course, user, user_certificate):
    """
    Tracks web certificate view related events.
    """
    # Badge Request Event Tracking Logic
    course_key = course.location.course_key

    if 'evidence_visit' in request.GET:
        badge_class = get_completion_badge(course_key, user)
        if not badge_class:
            log.warning(u'Visit to evidence URL for badge, but badges not configured for course "%s"', course_key)
            badges = []
        else:
            badges = badge_class.get_for_user(user)
        if badges:
            # There should only ever be one of these.
            badge = badges[0]
            tracker.emit(
                'edx.badge.assertion.evidence_visited',
                {
                    'badge_name': badge.badge_class.display_name,
                    'badge_slug': badge.badge_class.slug,
                    'badge_generator': badge.backend,
                    'issuing_component': badge.badge_class.issuing_component,
                    'user_id': user.id,
                    'course_id': six.text_type(course_key),
                    'enrollment_mode': badge.badge_class.mode,
                    'assertion_id': badge.id,
                    'assertion_image_url': badge.image_url,
                    'assertion_json_url': badge.assertion_url,
                    'issuer': badge.data.get('issuer'),
                }
            )
        else:
            log.warning(
                u"Could not find badge for %s on course %s.",
                user.id,
                course_key,
            )

    # track certificate evidence_visited event for analytics when certificate_user and accessing_user are different
    if request.user and request.user.id != user.id:
        emit_certificate_event('evidence_visited', user, six.text_type(course.id), course, {
            'certificate_id': user_certificate.verify_uuid,
            'enrollment_mode': user_certificate.mode,
            'social_network': CertificateSocialNetworks.linkedin
        })


def _update_badge_context(context, course, user):
    """
    Updates context with badge info.
    """
    badge = None
    if badges_enabled() and course.issue_badges:
        badges = get_completion_badge(course.location.course_key, user).get_for_user(user)
        if badges:
            badge = badges[0]
    context['badge'] = badge


def _update_organization_context(context, course):
    """
    Updates context with organization related info.
    """
    partner_long_name, organization_logo = None, None
    partner_short_name = course.display_organization if course.display_organization else course.org
    organizations = organization_api.get_course_organizations(course_id=course.id)
    if organizations:
        #TODO Need to add support for multiple organizations, Currently we are interested in the first one.
        organization = organizations[0]
        partner_long_name = organization.get('name', partner_long_name)
        partner_short_name = organization.get('short_name', partner_short_name)
        organization_logo = organization.get('logo', None)

    context['organization_long_name'] = partner_long_name
    context['organization_short_name'] = partner_short_name
    context['accomplishment_copy_course_org'] = partner_short_name
    context['organization_logo'] = organization_logo


def unsupported_url(request, user_id, course_id):
    """
    This view returns the un-supported url page aimed to let the user aware that
    url is no longer supported
    """
    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)
    configuration = CertificateHtmlViewConfiguration.get_config()
    return _render_invalid_certificate(
        request, course_id, platform_name, configuration, cert_path='certificates/url_unsupported.html'
    )


@login_required
def render_preview_certificate(request, course_id):
    """
    This view renders the course certificate in preview mode
    """
    return render_html_view(request, six.text_type(course_id))


def render_cert_by_uuid(request, certificate_uuid):
    """
    This public view generates an HTML representation of the specified certificate
    """
    try:
        certificate = GeneratedCertificate.eligible_certificates.get(
            verify_uuid=certificate_uuid,
            status=CertificateStatuses.downloadable
        )
        return render_html_view(request, six.text_type(certificate.course_id), certificate)
    except GeneratedCertificate.DoesNotExist:
        raise Http404


@handle_500(
    template_path="certificates/server-error.html",
    test_func=lambda request: request.GET.get('preview', None)
)
def render_html_view(request, course_id, certificate=None):
    """
    This public view generates an HTML representation of the specified user and course
    If a certificate is not available, we display a "Sorry!" screen instead
    """
    user = certificate.user if certificate else request.user
    user_id = user.id
    preview_mode = request.GET.get('preview', None)
    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)
    configuration = CertificateHtmlViewConfiguration.get_config()

    # Kick the user back to the "Invalid" screen if the feature is disabled globally
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return _render_invalid_certificate(request, course_id, platform_name, configuration)

    # Load the course and user objects
    try:
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)

    # For any course or user exceptions, kick the user back to the "Invalid" screen
    except (InvalidKeyError, Http404) as exception:
        error_str = (
            u"Invalid cert: error finding course %s "
            u"Specific error: %s"
        )
        log.info(error_str, course_id, str(exception))
        return _render_invalid_certificate(request, course_id, platform_name, configuration)

    # Kick the user back to the "Invalid" screen if the feature is disabled for the course
    if not course.cert_html_view_enabled:
        log.info(
            u"Invalid cert: HTML certificates disabled for %s. User id: %d",
            course_id,
            user_id,
        )
        return _render_invalid_certificate(request, course_id, platform_name, configuration)

    # Load user's certificate
    user_certificate = _get_user_certificate(request, user, course_key, course, preview_mode)
    if not user_certificate:
        log.info(
            u"Invalid cert: User %d does not have eligible cert for %s.",
            user_id,
            course_id,
        )
        return _render_invalid_certificate(request, course_id, platform_name, configuration)

    # Get the active certificate configuration for this course
    # If we do not have an active certificate, we'll need to send the user to the "Invalid" screen
    # Passing in the 'preview' parameter, if specified, will return a configuration, if defined
    active_configuration = get_active_web_certificate(course, preview_mode)
    if active_configuration is None:
        log.info(
            u"Invalid cert: course %s does not have an active configuration. User id: %d",
            course_id,
            user_id,
        )
        return _render_invalid_certificate(request, course_id, platform_name, configuration)

    # Get data from Discovery service that will be necessary for rendering this Certificate.
    catalog_data = _get_catalog_data_for_course(course_key)

    # Determine whether to use the standard or custom template to render the certificate.
    custom_template = None
    custom_template_language = None
    if settings.FEATURES.get('CUSTOM_CERTIFICATE_TEMPLATES_ENABLED', False):
        log.info(u"Custom certificate for course %s", course_id)
        custom_template, custom_template_language = _get_custom_template_and_language(
            course.id,
            user_certificate.mode,
            catalog_data.pop('content_language', None)
        )

    # Determine the language that should be used to render the certificate.
    # For the standard certificate template, use the user language. For custom templates, use
    # the language associated with the template.
    user_language = translation.get_language()
    certificate_language = custom_template_language if custom_template else user_language

    log.info(
        u"certificate language is: %s for the course: %s",
        certificate_language,
        course_key
    )

    # Generate the certificate context in the correct language, then render the template.
    with translation.override(certificate_language):
        context = {'user_language': user_language}

        _update_context_with_basic_info(context, course_id, platform_name, configuration)

        context['certificate_data'] = active_configuration

        # Append/Override the existing view context values with any mode-specific ConfigurationModel values
        context.update(configuration.get(user_certificate.mode, {}))

        # Append organization info
        _update_organization_context(context, course)

        # Append course info
        _update_course_context(request, context, course, course_key, platform_name)

        # Append course run info from discovery
        context.update(catalog_data)

        # Append user info
        _update_context_with_user_info(context, user, user_certificate)

        # Append social sharing info
        _update_social_context(request, context, course, user, user_certificate, platform_name)

        # Append/Override the existing view context values with certificate specific values
        _update_certificate_context(context, course, user_certificate, platform_name)

        # Append badge info
        _update_badge_context(context, course, user)

        # Add certificate header/footer data to current context
        context.update(get_certificate_header_context(is_secure=request.is_secure()))
        context.update(get_certificate_footer_context())

        # Append/Override the existing view context values with any course-specific static values from Advanced Settings
        context.update(course.cert_html_view_overrides)

        # Track certificate view events
        _track_certificate_events(request, context, course, user, user_certificate)

        # Render the certificate
        return _render_valid_certificate(request, context, custom_template)


def _get_catalog_data_for_course(course_key):
    """
    Retrieve data from the Discovery service necessary for rendering a certificate for a specific course.
    """
    course_certificate_settings = CertificateGenerationCourseSetting.get(course_key)
    if not course_certificate_settings:
        return {}

    catalog_data = {}
    course_run_fields = []
    if course_certificate_settings.language_specific_templates_enabled:
        course_run_fields.append('content_language')
    if course_certificate_settings.include_hours_of_effort:
        course_run_fields.extend(['weeks_to_complete', 'max_effort'])

    if course_run_fields:
        course_run_data = get_course_run_details(course_key, course_run_fields)
        if course_run_data.get('weeks_to_complete') and course_run_data.get('max_effort'):
            try:
                weeks_to_complete = int(course_run_data['weeks_to_complete'])
                max_effort = int(course_run_data['max_effort'])
                catalog_data['hours_of_effort'] = weeks_to_complete * max_effort
            except ValueError:
                log.exception('Error occurred while parsing course run details')
        catalog_data['content_language'] = course_run_data.get('content_language')
    log.info(
        u"catalog data received for course: %s is : %s",
        course_key,
        catalog_data,
    )
    return catalog_data


def _get_custom_template_and_language(course_id, course_mode, course_language):
    """
    Return the custom certificate template, if any, that should be rendered for the provided course/mode/language
    combination, along with the language that should be used to render that template.
    """
    closest_released_language = get_closest_released_language(course_language) if course_language else None
    log.info(
        u"closest released language for %s is %s and course language was: %s",
        course_id,
        closest_released_language,
        course_language
    )
    template = get_certificate_template(course_id, course_mode, closest_released_language)

    if template and template.language:
        return (template, closest_released_language)
    elif template:
        user_language = translation.get_language()
        return (template, user_language)
    else:
        return (None, None)


def _render_invalid_certificate(request, course_id, platform_name, configuration,
                                cert_path=INVALID_CERTIFICATE_TEMPLATE_PATH):
    """
    Renders the invalid certificate view with default header and footer.
    """
    context = {}
    _update_context_with_basic_info(context, course_id, platform_name, configuration)
    # Add certificate header/footer data to current context
    context.update(get_certificate_header_context(is_secure=request.is_secure()))
    context.update(get_certificate_footer_context())
    return render_to_response(cert_path, context)


def _render_valid_certificate(request, context, custom_template=None):
    if custom_template:
        template = Template(
            custom_template.template,
            output_encoding='utf-8',
            input_encoding='utf-8',
            default_filters=['decode.utf8'],
            encoding_errors='replace',
        )
        context = RequestContext(request, context)
        return HttpResponse(template.render(context))
    else:
        return render_to_response("certificates/valid.html", context)
