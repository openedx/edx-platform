# pylint: disable=bad-continuation
"""
Certificate HTML webview.
"""
from datetime import datetime
from uuid import uuid4
import logging
import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse

from courseware.access import has_access
from edxmako.shortcuts import render_to_response
from edxmako.template import Template
from eventtracking import tracker
from microsite_configuration import microsite
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.courses import course_image_url
from student.models import LinkedInAddToProfileConfiguration
from util import organizations_helpers as organization_api
from util.views import handle_500
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from certificates.api import (
    get_active_web_certificate,
    get_certificate_url,
    emit_certificate_event,
    has_html_certificates_enabled,
    get_certificate_template,
    get_certificate_header_context,
    get_certificate_footer_context,
)
from certificates.models import (
    GeneratedCertificate,
    CertificateStatuses,
    CertificateHtmlViewConfiguration,
    CertificateSocialNetworks,
    BadgeAssertion
)

log = logging.getLogger(__name__)


def get_certificate_description(mode, certificate_type, platform_name):
    """
    :return certificate_type_description on the basis of current mode
    """
    certificate_type_description = None
    if mode == 'honor':
        # Translators:  This text describes the 'Honor' course certificate type.
        certificate_type_description = _("An {cert_type} certificate signifies that a "
                                         "learner has agreed to abide by the honor code established by {platform_name} "
                                         "and has completed all of the required tasks for this course under its "
                                         "guidelines.").format(cert_type=certificate_type,
                                                               platform_name=platform_name)
    elif mode == 'verified':
        # Translators:  This text describes the 'ID Verified' course certificate type, which is a higher level of
        # verification offered by edX.  This type of verification is useful for professional education/certifications
        certificate_type_description = _("A {cert_type} certificate signifies that a "
                                         "learner has agreed to abide by the honor code established by {platform_name} "
                                         "and has completed all of the required tasks for this course under its "
                                         "guidelines. A {cert_type} certificate also indicates that the "
                                         "identity of the learner has been checked and "
                                         "is valid.").format(cert_type=certificate_type,
                                                             platform_name=platform_name)
    elif mode == 'xseries':
        # Translators:  This text describes the 'XSeries' course certificate type.  An XSeries is a collection of
        # courses related to each other in a meaningful way, such as a specific topic or theme, or even an organization
        certificate_type_description = _("An {cert_type} certificate demonstrates a high level of "
                                         "achievement in a program of study, and includes verification of "
                                         "the student's identity.").format(cert_type=certificate_type)
    return certificate_type_description


def _update_certificate_context(context, user_certificate, platform_name):
    """
    Build up the certificate web view context using the provided values
    (Helper method to keep the view clean)
    """
    # Populate dynamic output values using the course/certificate data loaded above
    certificate_type = context.get('certificate_type')

    # Override the defaults with any mode-specific static values
    context['certificate_id_number'] = user_certificate.verify_uuid
    context['certificate_verify_url'] = "{prefix}{uuid}{suffix}".format(
        prefix=context.get('certificate_verify_url_prefix'),
        uuid=user_certificate.verify_uuid,
        suffix=context.get('certificate_verify_url_suffix')
    )

    # Translators:  The format of the date includes the full name of the month
    context['certificate_date_issued'] = _('{month} {day}, {year}').format(
        month=user_certificate.modified_date.strftime("%B"),
        day=user_certificate.modified_date.day,
        year=user_certificate.modified_date.year
    )

    # Translators:  This text represents the verification of the certificate
    context['document_meta_description'] = _('This is a valid {platform_name} certificate for {user_name}, '
                                             'who participated in {partner_short_name} {course_number}').format(
        platform_name=platform_name,
        user_name=context['accomplishment_copy_name'],
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number']
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears in the browser title bar
    context['document_title'] = _("{partner_short_name} {course_number} Certificate | {platform_name}").format(
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number'],
        platform_name=platform_name
    )

    # Translators:  This text fragment appears after the student's name (displayed in a large font) on the certificate
    # screen.  The text describes the accomplishment represented by the certificate information displayed to the user
    context['accomplishment_copy_description_full'] = _("successfully completed, received a passing grade, and was "
                                                        "awarded this {platform_name} {certificate_type} "
                                                        "Certificate of Completion in ").format(
        platform_name=platform_name,
        certificate_type=context.get("certificate_type"))

    certificate_type_description = get_certificate_description(user_certificate.mode, certificate_type, platform_name)
    if certificate_type_description:
        context['certificate_type_description'] = certificate_type_description

    # Translators: This text describes the purpose (and therefore, value) of a course certificate
    context['certificate_info_description'] = _("{platform_name} acknowledges achievements through "
                                                "certificates, which are awarded for course activities "
                                                "that {platform_name} students complete.").format(
        platform_name=platform_name,
        tos_url=context.get('company_tos_url'),
        verified_cert_url=context.get('company_verified_certificate_url'))


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
        year=settings.COPYRIGHT_YEAR,
        platform_name=platform_name,
        reserved=reserved
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears
    # in the browser title bar when a requested certificate is not found or recognized
    context['document_title'] = _("Invalid Certificate")

    # Translators: The &amp; characters represent an ampersand character and can be ignored
    context['company_tos_urltext'] = _("Terms of Service &amp; Honor Code")

    # Translators: A 'Privacy Policy' is a legal document/statement describing a website's use of personal information
    context['company_privacy_urltext'] = _("Privacy Policy")

    # Translators: This line appears as a byline to a header image and describes the purpose of the page
    context['logo_subtitle'] = _("Certificate Validation")

    # Translators: Accomplishments describe the awards/certifications obtained by students on this platform
    context['accomplishment_copy_about'] = _('About {platform_name} Accomplishments').format(
        platform_name=platform_name
    )

    # Translators:  This line appears on the page just before the generation date for the certificate
    context['certificate_date_issued_title'] = _("Issued On:")

    # Translators:  The Certificate ID Number is an alphanumeric value unique to each individual certificate
    context['certificate_id_number_title'] = _('Certificate ID Number')

    context['certificate_info_title'] = _('About {platform_name} Certificates').format(
        platform_name=platform_name
    )

    context['certificate_verify_title'] = _("How {platform_name} Validates Student Certificates").format(
        platform_name=platform_name
    )

    # Translators:  This text describes the validation mechanism for a certificate file (known as GPG security)
    context['certificate_verify_description'] = _('Certificates issued by {platform_name} are signed by a gpg key so '
                                                  'that they can be validated independently by anyone with the '
                                                  '{platform_name} public key. For independent verification, '
                                                  '{platform_name} uses what is called a '
                                                  '"detached signature"&quot;".').format(platform_name=platform_name)

    context['certificate_verify_urltext'] = _("Validate this certificate for yourself")

    # Translators:  This text describes (at a high level) the mission and charter the edX platform and organization
    context['company_about_description'] = _("{platform_name} offers interactive online classes and MOOCs.").format(
        platform_name=platform_name)

    context['company_about_title'] = _("About {platform_name}").format(platform_name=platform_name)

    context['company_about_urltext'] = _("Learn more about {platform_name}").format(platform_name=platform_name)

    context['company_courselist_urltext'] = _("Learn with {platform_name}").format(platform_name=platform_name)

    context['company_careers_urltext'] = _("Work at {platform_name}").format(platform_name=platform_name)

    context['company_contact_urltext'] = _("Contact {platform_name}").format(platform_name=platform_name)

    # Translators:  This text appears near the top of the certficate and describes the guarantee provided by edX
    context['document_banner'] = _("{platform_name} acknowledges the following student accomplishment").format(
        platform_name=platform_name
    )


def _update_course_context(request, context, course, platform_name):
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
        context['accomplishment_copy_course_description'] = _('a course of study offered by {partner_long_name}.').format(
            partner_long_name=context['organization_long_name'],
            platform_name=platform_name)
    else:
        # Translators:  This text represents the description of course
        context['accomplishment_copy_course_description'] = _('a course of study offered by {partner_short_name}.').format(
            partner_short_name=context['organization_short_name'],
            platform_name=platform_name)


def _update_social_context(request, context, course, user, user_certificate, platform_name):
    """
    Updates context dictionary with info required for social sharing.
    """
    share_settings = microsite.get_value("SOCIAL_SHARING_SETTINGS", settings.SOCIAL_SHARING_SETTINGS)
    context['facebook_share_enabled'] = share_settings.get('CERTIFICATE_FACEBOOK', False)
    context['facebook_app_id'] = microsite.get_value("FACEBOOK_APP_ID", settings.FACEBOOK_APP_ID)
    context['facebook_share_text'] = share_settings.get(
        'CERTIFICATE_FACEBOOK_TEXT',
        _("I completed the {course_title} course on {platform_name}.").format(
            course_title=context['accomplishment_copy_course_name'],
            platform_name=platform_name
        )
    )
    context['twitter_share_enabled'] = share_settings.get('CERTIFICATE_TWITTER', False)
    context['twitter_share_text'] = share_settings.get(
        'CERTIFICATE_TWITTER_TEXT',
        _("I completed a course at {platform_name}. Take a look at my certificate.").format(
            platform_name=platform_name
        )
    )

    share_url = request.build_absolute_uri(get_certificate_url(course_id=course.id, uuid=user_certificate.verify_uuid))
    context['share_url'] = share_url
    twitter_url = ''
    if context.get('twitter_share_enabled', False):
        twitter_url = 'https://twitter.com/intent/tweet?text={twitter_share_text}&url={share_url}'.format(
            twitter_share_text=smart_str(context['twitter_share_text']),
            share_url=urllib.quote_plus(smart_str(share_url))
        )
    context['twitter_url'] = twitter_url
    context['linked_in_url'] = None
    # If enabled, show the LinkedIn "add to profile" button
    # Clicking this button sends the user to LinkedIn where they
    # can add the certificate information to their profile.
    linkedin_config = LinkedInAddToProfileConfiguration.current()
    linkedin_share_enabled = share_settings.get('CERTIFICATE_LINKEDIN', linkedin_config.enabled)
    if linkedin_share_enabled:
        context['linked_in_url'] = linkedin_config.add_to_profile_url(
            course.id,
            course.display_name,
            user_certificate.mode,
            smart_str(share_url)
        )


def _update_context_with_user_info(context, user, user_certificate):
    """
    Updates context dictionary with user related info.
    """
    user_fullname = user.profile.name
    context['username'] = user.username
    context['course_mode'] = user_certificate.mode
    context['accomplishment_user_id'] = user.id
    context['accomplishment_copy_name'] = user_fullname
    context['accomplishment_copy_username'] = user.username

    context['accomplishment_more_title'] = _("More Information About {user_name}'s Certificate:").format(
        user_name=user_fullname
    )
    # Translators: This line is displayed to a user who has completed a course and achieved a certification
    context['accomplishment_banner_opening'] = _("{fullname}, you earned a certificate!").format(
        fullname=user_fullname
    )

    # Translators: This line congratulates the user and instructs them to share their accomplishment on social networks
    context['accomplishment_banner_congrats'] = _("Congratulations! This page summarizes what "
                                                  "you accomplished. Show it off to family, friends, and colleagues "
                                                  "in your social and professional networks.")

    # Translators: This line leads the reader to understand more about the certificate that a student has been awarded
    context['accomplishment_copy_more_about'] = _("More about {fullname}'s accomplishment").format(
        fullname=user_fullname
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
        if has_access(request.user, 'instructor', course) or has_access(request.user, 'staff', course):
            user_certificate = GeneratedCertificate(
                mode=preview_mode,
                verify_uuid=unicode(uuid4().hex),
                modified_date=datetime.now().date()
            )
    else:
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
    badge = context['badge']
    # Badge Request Event Tracking Logic
    if 'evidence_visit' in request.GET and badge:
        tracker.emit(
            'edx.badge.assertion.evidence_visited',
            {
                'user_id': user.id,
                'course_id': unicode(course.id),
                'enrollment_mode': badge.mode,
                'assertion_id': badge.id,
                'assertion_image_url': badge.data['image'],
                'assertion_json_url': badge.data['json']['id'],
                'issuer': badge.data['issuer'],
            }
        )

    # track certificate evidence_visited event for analytics when certificate_user and accessing_user are different
    if request.user and request.user.id != user.id:
        emit_certificate_event('evidence_visited', user, unicode(course.id), course, {
            'certificate_id': user_certificate.verify_uuid,
            'enrollment_mode': user_certificate.mode,
            'social_network': CertificateSocialNetworks.linkedin
        })


def _render_certificate_template(request, context, course, user_certificate):
    """
    Picks appropriate certificate templates and renders it.
    """
    if settings.FEATURES.get('CUSTOM_CERTIFICATE_TEMPLATES_ENABLED', False):
        custom_template = get_certificate_template(course.id, user_certificate.mode)
        if custom_template:
            template = Template(
                custom_template,
                output_encoding='utf-8',
                input_encoding='utf-8',
                default_filters=['decode.utf8'],
                encoding_errors='replace',
            )
            context = RequestContext(request, context)
            return HttpResponse(template.render(context))

    return render_to_response("certificates/valid.html", context)


def _update_microsite_context(context, configuration):
    """
    Updates context with microsites data.
    Microsites will need to be able to override any hard coded
    content that was put into the context in the
    _update_certificate_context() call above. For example the
    'company_about_description' talks about edX, which we most likely
    do not want to keep in a microsite
    So we need to re-apply any configuration/content that
    we are sourcing from the database. This is somewhat duplicative of
    the code at the beginning of this method, but we
    need the configuration at the top as some error code paths
    require that to be set up early on in the pipeline
    """

    microsite_config_key = microsite.get_value('domain_prefix')
    microsites_config = configuration.get("microsites", {})
    if microsite_config_key and microsites_config:
        context.update(microsites_config.get(microsite_config_key, {}))


def _update_badge_context(context, course, user):
    """
    Updates context with badge info.
    """
    try:
        badge = BadgeAssertion.objects.get(user=user, course_id=course.location.course_key)
    except BadgeAssertion.DoesNotExist:
        badge = None
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


def render_cert_by_uuid(request, certificate_uuid):
    """
    This public view generates an HTML representation of the specified certificate
    """
    try:
        certificate = GeneratedCertificate.eligible_certificates.get(
            verify_uuid=certificate_uuid,
            status=CertificateStatuses.downloadable
        )
        return render_html_view(request, certificate.user.id, unicode(certificate.course_id))
    except GeneratedCertificate.DoesNotExist:
        raise Http404


@handle_500(
    template_path="certificates/server-error.html",
    test_func=lambda request: request.GET.get('preview', None)
)
def render_html_view(request, user_id, course_id):
    """
    This public view generates an HTML representation of the specified user and course
    If a certificate is not available, we display a "Sorry!" screen instead
    """
    preview_mode = request.GET.get('preview', None)
    platform_name = microsite.get_value("platform_name", settings.PLATFORM_NAME)
    configuration = CertificateHtmlViewConfiguration.get_config()
    # Create the initial view context, bootstrapping with Django settings and passed-in values
    context = {}
    _update_context_with_basic_info(context, course_id, platform_name, configuration)
    invalid_template_path = 'certificates/invalid.html'

    # Kick the user back to the "Invalid" screen if the feature is disabled
    if not has_html_certificates_enabled(course_id):
        return render_to_response(invalid_template_path, context)

    # Load the course and user objects
    try:
        course_key = CourseKey.from_string(course_id)
        user = User.objects.get(id=user_id)
        course = modulestore().get_course(course_key)

    # For any other expected exceptions, kick the user back to the "Invalid" screen
    except (InvalidKeyError, ItemNotFoundError, User.DoesNotExist):
        return render_to_response(invalid_template_path, context)

    # Load user's certificate
    user_certificate = _get_user_certificate(request, user, course_key, course, preview_mode)
    if not user_certificate:
        return render_to_response(invalid_template_path, context)

    # Get the active certificate configuration for this course
    # If we do not have an active certificate, we'll need to send the user to the "Invalid" screen
    # Passing in the 'preview' parameter, if specified, will return a configuration, if defined
    active_configuration = get_active_web_certificate(course, preview_mode)
    if active_configuration is None:
        return render_to_response(invalid_template_path, context)
    context['certificate_data'] = active_configuration

    # Append/Override the existing view context values with any mode-specific ConfigurationModel values
    context.update(configuration.get(user_certificate.mode, {}))

    # Append organization info
    _update_organization_context(context, course)

    # Append course info
    _update_course_context(request, context, course, platform_name)

    # Append user info
    _update_context_with_user_info(context, user, user_certificate)

    # Append social sharing info
    _update_social_context(request, context, course, user, user_certificate, platform_name)

    # Append/Override the existing view context values with certificate specific values
    _update_certificate_context(context, user_certificate, platform_name)

    # Append badge info
    _update_badge_context(context, course, user)

    # Append microsite overrides
    _update_microsite_context(context, configuration)

    # Add certificate header/footer data to current context
    context.update(get_certificate_header_context(is_secure=request.is_secure()))
    context.update(get_certificate_footer_context())

    # Append/Override the existing view context values with any course-specific static values from Advanced Settings
    context.update(course.cert_html_view_overrides)

    # Track certificate view events
    _track_certificate_events(request, context, course, user, user_certificate)

    # FINALLY, render appropriate certificate
    return _render_certificate_template(request, context, course, user_certificate)
