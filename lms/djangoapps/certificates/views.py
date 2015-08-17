"""URL handlers related to certificate handling by LMS"""
from microsite_configuration import microsite
from datetime import datetime
from uuid import uuid4
from django.shortcuts import redirect, get_object_or_404
from opaque_keys.edx.locator import CourseLocator
from eventtracking import tracker
import dogstats_wrapper as dog_stats_api
import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from capa.xqueue_interface import XQUEUE_METRIC_NAME
from certificates.api import (
    get_active_web_certificate,
    get_certificate_url,
    generate_user_certificates,
    emit_certificate_event
)
from certificates.models import (
    certificate_status_for_student,
    CertificateStatuses,
    GeneratedCertificate,
    ExampleCertificate,
    CertificateHtmlViewConfiguration,
    CertificateSocialNetworks,
    BadgeAssertion
)
from edxmako.shortcuts import render_to_response
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.models import LinkedInAddToProfileConfiguration
from util.json_request import JsonResponse, JsonResponseBadRequest
from util.bad_request_rate_limiter import BadRequestRateLimiter
from courseware.courses import course_image_url

logger = logging.getLogger(__name__)


class CourseDoesNotExist(Exception):
    """
    This exception is raised in the case where None is returned from the modulestore
    """
    pass


@csrf_exempt
def request_certificate(request):
    """Request the on-demand creation of a certificate for some user, course.

    A request doesn't imply a guarantee that such a creation will take place.
    We intentionally use the same machinery as is used for doing certification
    at the end of a course run, so that we can be sure users get graded and
    then if and only if they pass, do they get a certificate issued.
    """
    if request.method == "POST":
        if request.user.is_authenticated():
            username = request.user.username
            student = User.objects.get(username=username)
            course_key = SlashSeparatedCourseKey.from_deprecated_string(request.POST.get('course_id'))
            course = modulestore().get_course(course_key, depth=2)

            status = certificate_status_for_student(student, course_key)['status']
            if status in [CertificateStatuses.unavailable, CertificateStatuses.notpassing, CertificateStatuses.error]:
                log_msg = u'Grading and certification requested for user %s in course %s via /request_certificate call'
                logger.info(log_msg, username, course_key)
                status = generate_user_certificates(student, course_key, course=course)
            return HttpResponse(json.dumps({'add_status': status}), mimetype='application/json')
        return HttpResponse(json.dumps({'add_status': 'ERRORANONYMOUSUSER'}), mimetype='application/json')


@csrf_exempt
def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.

    See models.py for a state diagram of certificate states

    This view should only ever be accessed by the xqueue server
    """

    status = CertificateStatuses
    if request.method == "POST":

        xqueue_body = json.loads(request.POST.get('xqueue_body'))
        xqueue_header = json.loads(request.POST.get('xqueue_header'))

        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(xqueue_body['course_id'])

            cert = GeneratedCertificate.objects.get(
                user__username=xqueue_body['username'],
                course_id=course_key,
                key=xqueue_header['lms_key'])

        except GeneratedCertificate.DoesNotExist:
            logger.critical('Unable to lookup certificate\n'
                            'xqueue_body: {0}\n'
                            'xqueue_header: {1}'.format(
                                xqueue_body, xqueue_header))

            return HttpResponse(json.dumps({
                'return_code': 1,
                'content': 'unable to lookup key'}),
                mimetype='application/json')

        if 'error' in xqueue_body:
            cert.status = status.error
            if 'error_reason' in xqueue_body:

                # Hopefully we will record a meaningful error
                # here if something bad happened during the
                # certificate generation process
                #
                # example:
                #  (aamorm BerkeleyX/CS169.1x/2012_Fall)
                #  <class 'simples3.bucket.S3Error'>:
                #  HTTP error (reason=error(32, 'Broken pipe'), filename=None) :
                #  certificate_agent.py:175

                cert.error_reason = xqueue_body['error_reason']
        else:
            if cert.status in [status.generating, status.regenerating]:
                cert.download_uuid = xqueue_body['download_uuid']
                cert.verify_uuid = xqueue_body['verify_uuid']
                cert.download_url = xqueue_body['url']
                cert.status = status.downloadable
            elif cert.status in [status.deleting]:
                cert.status = status.deleted
            else:
                logger.critical('Invalid state for cert update: {0}'.format(
                    cert.status))
                return HttpResponse(
                    json.dumps({
                        'return_code': 1,
                        'content': 'invalid cert status'
                    }),
                    mimetype='application/json'
                )

        dog_stats_api.increment(XQUEUE_METRIC_NAME, tags=[
            u'action:update_certificate',
            u'course_id:{}'.format(cert.course_id)
        ])

        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),
                            mimetype='application/json')


@csrf_exempt
@require_POST
def update_example_certificate(request):
    """Callback from the XQueue that updates example certificates.

    Example certificates are used to verify that certificate
    generation is configured correctly for a course.

    Unlike other certificates, example certificates
    are not associated with a particular user or displayed
    to students.

    For this reason, we need a different end-point to update
    the status of generated example certificates.

    Arguments:
        request (HttpRequest)

    Returns:
        HttpResponse (200): Status was updated successfully.
        HttpResponse (400): Invalid parameters.
        HttpResponse (403): Rate limit exceeded for bad requests.
        HttpResponse (404): Invalid certificate identifier or access key.

    """
    logger.info(u"Received response for example certificate from XQueue.")

    rate_limiter = BadRequestRateLimiter()

    # Check the parameters and rate limits
    # If these are invalid, return an error response.
    if rate_limiter.is_rate_limit_exceeded(request):
        logger.info(u"Bad request rate limit exceeded for update example certificate end-point.")
        return HttpResponseForbidden("Rate limit exceeded")

    if 'xqueue_body' not in request.POST:
        logger.info(u"Missing parameter 'xqueue_body' for update example certificate end-point")
        rate_limiter.tick_bad_request_counter(request)
        return JsonResponseBadRequest("Parameter 'xqueue_body' is required.")

    if 'xqueue_header' not in request.POST:
        logger.info(u"Missing parameter 'xqueue_header' for update example certificate end-point")
        rate_limiter.tick_bad_request_counter(request)
        return JsonResponseBadRequest("Parameter 'xqueue_header' is required.")

    try:
        xqueue_body = json.loads(request.POST['xqueue_body'])
        xqueue_header = json.loads(request.POST['xqueue_header'])
    except (ValueError, TypeError):
        logger.info(u"Could not decode params to example certificate end-point as JSON.")
        rate_limiter.tick_bad_request_counter(request)
        return JsonResponseBadRequest("Parameters must be JSON-serialized.")

    # Attempt to retrieve the example certificate record
    # so we can update the status.
    try:
        uuid = xqueue_body.get('username')
        access_key = xqueue_header.get('lms_key')
        cert = ExampleCertificate.objects.get(uuid=uuid, access_key=access_key)
    except ExampleCertificate.DoesNotExist:
        # If we are unable to retrieve the record, it means the uuid or access key
        # were not valid.  This most likely means that the request is NOT coming
        # from the XQueue.  Return a 404 and increase the bad request counter
        # to protect against a DDOS attack.
        logger.info(u"Could not find example certificate with uuid '%s' and access key '%s'", uuid, access_key)
        rate_limiter.tick_bad_request_counter(request)
        raise Http404

    if 'error' in xqueue_body:
        # If an error occurs, save the error message so we can fix the issue.
        error_reason = xqueue_body.get('error_reason')
        cert.update_status(ExampleCertificate.STATUS_ERROR, error_reason=error_reason)
        logger.warning(
            (
                u"Error occurred during example certificate generation for uuid '%s'.  "
                u"The error response was '%s'."
            ), uuid, error_reason
        )
    else:
        # If the certificate generated successfully, save the download URL
        # so we can display the example certificate.
        download_url = xqueue_body.get('url')
        if download_url is None:
            rate_limiter.tick_bad_request_counter(request)
            logger.warning(u"No download URL provided for example certificate with uuid '%s'.", uuid)
            return JsonResponseBadRequest(
                "Parameter 'download_url' is required for successfully generated certificates."
            )
        else:
            cert.update_status(ExampleCertificate.STATUS_SUCCESS, download_url=download_url)
            logger.info("Successfully updated example certificate with uuid '%s'.", uuid)

    # Let the XQueue know that we handled the response
    return JsonResponse({'return_code': 0})


def get_certificate_description(mode, certificate_type, platform_name):
    """
    :return certificate_type_description on the basis of current mode
    """
    certificate_type_description = None
    if mode == 'honor':
        # Translators:  This text describes the 'Honor' course certificate type.
        certificate_type_description = _("An {cert_type} Certificate signifies that an {platform_name} "
                                         "learner has agreed to abide by {platform_name}'s honor code and "
                                         "completed all of the required tasks for this course under its "
                                         "guidelines.").format(cert_type=certificate_type,
                                                               platform_name=platform_name)
    elif mode == 'verified':
        # Translators:  This text describes the 'ID Verified' course certificate type, which is a higher level of
        # verification offered by edX.  This type of verification is useful for professional education/certifications
        certificate_type_description = _("An {cert_type} Certificate signifies that an {platform_name} "
                                         "learner has agreed to abide by {platform_name}'s honor code and "
                                         "completed all of the required tasks for this course under its "
                                         "guidelines, as well as having their photo ID checked to verify "
                                         "their identity.").format(cert_type=certificate_type,
                                                                   platform_name=platform_name)
    elif mode == 'xseries':
        # Translators:  This text describes the 'XSeries' course certificate type.  An XSeries is a collection of
        # courses related to each other in a meaningful way, such as a specific topic or theme, or even an organization
        certificate_type_description = _("An {cert_type} Certificate demonstrates a high level of "
                                         "achievement in a program of study, and includes verification of "
                                         "the student's identity.").format(cert_type=certificate_type)
    return certificate_type_description


# pylint: disable=bad-continuation
def _update_certificate_context(context, course, user, user_certificate):
    """
    Build up the certificate web view context using the provided values
    (Helper method to keep the view clean)
    """
    # Populate dynamic output values using the course/certificate data loaded above
    user_fullname = user.profile.name
    platform_name = microsite.get_value("platform_name", settings.PLATFORM_NAME)
    certificate_type = context.get('certificate_type')

    context['username'] = user.username
    context['course_mode'] = user_certificate.mode
    context['accomplishment_user_id'] = user.id
    context['accomplishment_copy_name'] = user_fullname
    context['accomplishment_copy_username'] = user.username
    context['accomplishment_copy_course_org'] = course.org
    context['accomplishment_copy_course_name'] = course.display_name
    context['course_image_url'] = course_image_url(course)
    context['share_settings'] = settings.FEATURES.get('SOCIAL_SHARING_SETTINGS', {})
    try:
        badge = BadgeAssertion.objects.get(user=user, course_id=course.location.course_key)
    except BadgeAssertion.DoesNotExist:
        badge = None
    context['badge'] = badge

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

    accd_course_org_html = '<span class="detail--xuniversity">{partner_name}</span>'.format(partner_name=course.org)
    accd_platform_name_html = '<span class="detail--company">{platform_name}</span>'.format(platform_name=platform_name)
    # Translators: This line appears on the certificate after the name of a course, and provides more
    # information about the organizations providing the course material to platform users
    context['accomplishment_copy_course_description'] = _('a course of study offered by {partner_name}, '
                                                          'through {platform_name}.').format(
        partner_name=accd_course_org_html,
        platform_name=accd_platform_name_html
    )

    # Translators: Accomplishments describe the awards/certifications obtained by students on this platform
    context['accomplishment_copy_about'] = _('About {platform_name} Accomplishments').format(
        platform_name=platform_name
    )

    context['accomplishment_more_title'] = _("More Information About {user_name}'s Certificate:").format(
        user_name=user_fullname
    )

    # Translators:  This line appears on the page just before the generation date for the certificate
    context['certificate_date_issued_title'] = _("Issued On:")

    # Translators:  The Certificate ID Number is an alphanumeric value unique to each individual certificate
    context['certificate_id_number_title'] = _('Certificate ID Number')

    context['certificate_info_title'] = _('About {platform_name} Certificates').format(
        platform_name=platform_name
    )

    # Translators: This text describes the purpose (and therefore, value) of a course certificate
    # 'verifying your identity' refers to the process for establishing the authenticity of the student
    context['certificate_info_description'] = _("{platform_name} acknowledges achievements through certificates, which "
                                                "are awarded for various activities {platform_name} students complete "
                                                "under the <a href='{tos_url}'>{platform_name} Honor Code</a>.  Some "
                                                "certificates require completing additional steps, such as "
                                                "<a href='{verified_cert_url}'> verifying your identity</a>.").format(
        platform_name=platform_name,
        tos_url=context.get('company_tos_url'),
        verified_cert_url=context.get('company_verified_certificate_url')
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
    context['company_about_description'] = _("{platform_name} offers interactive online classes and MOOCs from the "
                                             "world's best universities, including MIT, Harvard, Berkeley, University "
                                             "of Texas, and many others.  {platform_name} is a non-profit online "
                                             "initiative created by founding partners Harvard and MIT.").format(
        platform_name=platform_name
    )

    context['company_about_title'] = _("About {platform_name}").format(platform_name=platform_name)

    context['company_about_urltext'] = _("Learn more about {platform_name}").format(platform_name=platform_name)

    context['company_courselist_urltext'] = _("Learn with {platform_name}").format(platform_name=platform_name)

    context['company_careers_urltext'] = _("Work at {platform_name}").format(platform_name=platform_name)

    context['company_contact_urltext'] = _("Contact {platform_name}").format(platform_name=platform_name)

    # Translators:  This text appears near the top of the certficate and describes the guarantee provided by edX
    context['document_banner'] = _("{platform_name} acknowledges the following student accomplishment").format(
        platform_name=platform_name
    )

    # Translators:  This text represents the verification of the certificate
    context['document_meta_description'] = _('This is a valid {platform_name} certificate for {user_name}, '
                                             'who participated in {partner_name} {course_number}').format(
        platform_name=platform_name,
        user_name=user_fullname,
        partner_name=course.org,
        course_number=course.number
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears in the browser title bar
    context['document_title'] = _("{partner_name} {course_number} Certificate | {platform_name}").format(
        partner_name=course.org,
        course_number=course.number,
        platform_name=platform_name
    )

    # Translators:  This text fragment appears after the student's name (displayed in a large font) on the certificate
    # screen.  The text describes the accomplishment represented by the certificate information displayed to the user
    context['accomplishment_copy_description_full'] = _("successfully completed, received a passing grade, and was "
                                                        "awarded a {platform_name} {certificate_type} "
                                                        "Certificate of Completion in ").format(
        platform_name=platform_name,
        certificate_type=context.get("certificate_type")
    )

    certificate_type_description = get_certificate_description(user_certificate.mode, certificate_type, platform_name)
    if certificate_type_description:
        context['certificate_type_description'] = certificate_type_description

    # If enabled, show the LinkedIn "add to profile" button
    # Clicking this button sends the user to LinkedIn where they
    # can add the certificate information to their profile.
    linkedin_config = LinkedInAddToProfileConfiguration.current()
    if linkedin_config.enabled:
        context['linked_in_url'] = linkedin_config.add_to_profile_url(
            course.id,
            course.display_name,
            user_certificate.mode,
            get_certificate_url(
                user_id=user.id,
                course_id=unicode(course.id),
                verify_uuid=user_certificate.verify_uuid
            )
        )

    # Translators: This line is displayed to a user who has completed a course and achieved a certification
    context['accomplishment_banner_opening'] = _("{fullname}, you've earned a certificate!").format(
        fullname=user_fullname
    )

    # Translators: This line congratulates the user and instructs them to share their accomplishment on social networks
    context['accomplishment_banner_congrats'] = _("Congratulations! This page summarizes all of the details of what "
                                                  "you've accomplished. Show it off to family, friends, and colleagues "
                                                  "in your social and professional networks.")

    # Translators: This line leads the reader to understand more about the certificate that a student has been awarded
    context['accomplishment_copy_more_about'] = _("More about {fullname}'s accomplishment").format(
        fullname=user_fullname
    )


def render_html_view(request, user_id, course_id):
    """
    This public view generates an HTML representation of the specified student's certificate
    If a certificate is not available, we display a "Sorry!" screen instead
    """

    # Create the initial view context, bootstrapping with Django settings and passed-in values
    context = {}
    context['platform_name'] = microsite.get_value("platform_name", settings.PLATFORM_NAME)
    context['course_id'] = course_id

    # Update the view context with the default ConfigurationModel settings
    configuration = CertificateHtmlViewConfiguration.get_config()
    # if we are in a microsite, then let's first see if there is an override
    # section in our config
    config_key = microsite.get_value('microsite_config_key', 'default')
    # if there is no special microsite override, then let's use default
    if config_key not in configuration:
        config_key = 'default'
    context.update(configuration.get(config_key, {}))

    # Translators:  'All rights reserved' is a legal term used in copyrighting to protect published content
    reserved = _("All rights reserved")
    context['copyright_text'] = '&copy; {year} {platform_name}. {reserved}.'.format(
        year=settings.COPYRIGHT_YEAR,
        platform_name=context.get('platform_name'),
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
    invalid_template_path = 'certificates/invalid.html'

    # Kick the user back to the "Invalid" screen if the feature is disabled
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return render_to_response(invalid_template_path, context)

    # Load the core building blocks for the view context
    try:
        course_key = CourseKey.from_string(course_id)
        user = User.objects.get(id=user_id)
        course = modulestore().get_course(course_key)

        if not course:
            raise CourseDoesNotExist

        # Attempt to load the user's generated certificate data
        user_certificate = GeneratedCertificate.objects.get(
            user=user,
            course_id=course_key
        )

    # If there's no generated certificate data for this user, we need to see if we're in 'preview' mode...
    # If we are, we'll need to create a mock version of the user_certificate container for previewing
    except GeneratedCertificate.DoesNotExist:
        if request.GET.get('preview', None):
            user_certificate = GeneratedCertificate(
                mode=request.GET.get('preview'),
                verify_uuid=unicode(uuid4().hex),
                modified_date=datetime.now().date()
            )
        else:
            return render_to_response(invalid_template_path, context)

    # For any other expected exceptions, kick the user back to the "Invalid" screen
    except (InvalidKeyError, CourseDoesNotExist, User.DoesNotExist):
        return render_to_response(invalid_template_path, context)

    # Badge Request Event Tracking Logic
    if 'evidence_visit' in request.GET:
        try:
            badge = BadgeAssertion.objects.get(user=user, course_id=course_key)
            tracker.emit(
                'edx.badge.assertion.evidence_visited',
                {
                    'user_id': user.id,
                    'course_id': unicode(course_key),
                    'enrollment_mode': badge.mode,
                    'assertion_id': badge.id,
                    'assertion_image_url': badge.data['image'],
                    'assertion_json_url': badge.data['json']['id'],
                    'issuer': badge.data['issuer'],
                }
            )
        except BadgeAssertion.DoesNotExist:
            logger.warn(
                "Could not find badge for %s on course %s.",
                user.id,
                course_key,
            )

    # Okay, now we have all of the pieces, time to put everything together

    # Get the active certificate configuration for this course
    # If we do not have an active certificate, we'll need to send the user to the "Invalid" screen
    # Passing in the 'preview' parameter, if specified, will return a configuration, if defined
    active_configuration = get_active_web_certificate(course, request.GET.get('preview'))
    if active_configuration is None:
        return render_to_response(invalid_template_path, context)
    else:
        context['certificate_data'] = active_configuration

    # Append/Override the existing view context values with any mode-specific ConfigurationModel values
    context.update(configuration.get(user_certificate.mode, {}))

    # Append/Override the existing view context values with request-time values
    _update_certificate_context(context, course, user, user_certificate)

    # Microsites will need to be able to override any hard coded
    # content that was put into the context in the
    # _update_certificate_context() call above. For example the
    # 'company_about_description' talks about edX, which we most likely
    # do not want to keep in a microsite
    #
    # So we need to re-apply any configuration/content that
    # we are sourceing from the database. This is somewhat duplicative of
    # the code at the beginning of this method, but we
    # need the configuration at the top as some error code paths
    # require that to be set up early on in the pipeline
    #
    microsite_config_key = microsite.get_value('microsite_config_key')
    if microsite_config_key:
        context.update(configuration.get(microsite_config_key, {}))

    # track certificate evidence_visited event for analytics when certificate_user and accessing_user are different
    if request.user and request.user.id != user.id:
        emit_certificate_event('evidence_visited', user, course_id, course, {
            'certificate_id': user_certificate.verify_uuid,
            'enrollment_mode': user_certificate.mode,
            'social_network': CertificateSocialNetworks.linkedin
        })

    # Append/Override the existing view context values with any course-specific static values from Advanced Settings
    context.update(course.cert_html_view_overrides)

    # FINALLY, generate and send the output the client
    return render_to_response("certificates/valid.html", context)


@ensure_valid_course_key
def track_share_redirect(request__unused, course_id, network, student_username):
    """
    Tracks when a user downloads a badge for sharing.
    """
    course_id = CourseLocator.from_string(course_id)
    assertion = get_object_or_404(BadgeAssertion, user__username=student_username, course_id=course_id)
    tracker.emit(
        'edx.badge.assertion.shared', {
            'course_id': unicode(course_id),
            'social_network': network,
            'assertion_id': assertion.id,
            'assertion_json_url': assertion.data['json']['id'],
            'assertion_image_url': assertion.image_url,
            'user_id': assertion.user.id,
            'enrollment_mode': assertion.mode,
            'issuer': assertion.data['issuer'],
        }
    )
    return redirect(assertion.image_url)
