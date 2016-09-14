"""Interface for adding certificate generation tasks to the XQueue. """
import json
import random
import logging
import lxml.html
from lxml.etree import XMLSyntaxError, ParserError
from uuid import uuid4

from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse
from requests.auth import HTTPBasicAuth

from courseware import grades
from xmodule.modulestore.django import modulestore
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader, make_hashkey
from course_modes.models import CourseMode
from student.models import UserProfile, CourseEnrollment
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification

from certificates.models import (
    GeneratedCertificate,
    certificate_status_for_student,
    CertificateStatuses as status,
    CertificateWhitelist,
    ExampleCertificate
)


LOGGER = logging.getLogger(__name__)


class XQueueAddToQueueError(Exception):
    """An error occurred when adding a certificate task to the queue. """

    def __init__(self, error_code, error_msg):
        self.error_code = error_code
        self.error_msg = error_msg
        super(XQueueAddToQueueError, self).__init__(unicode(self))

    def __unicode__(self):
        return (
            u"Could not add certificate to the XQueue.  "
            u"The error code was '{code}' and the message was '{msg}'."
        ).format(
            code=self.error_code,
            msg=self.error_msg
        )


class XQueueCertInterface(object):
    """
    XQueueCertificateInterface provides an
    interface to the xqueue server for
    managing student certificates.

    Instantiating an object will create a new
    connection to the queue server.

    See models.py for valid state transitions,
    summary of methods:

       add_cert:   Add a new certificate.  Puts a single
                   request on the queue for the student/course.
                   Once the certificate is generated a post
                   will be made to the update_certificate
                   view which will save the certificate
                   download URL.

       regen_cert: Regenerate an existing certificate.
                   For a user that already has a certificate
                   this will delete the existing one and
                   generate a new cert.


       del_cert:   Delete an existing certificate
                   For a user that already has a certificate
                   this will delete his cert.

    """

    def __init__(self, request=None):

        # Get basic auth (username/password) for
        # xqueue connection if it's in the settings

        if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
            requests_auth = HTTPBasicAuth(
                *settings.XQUEUE_INTERFACE['basic_auth'])
        else:
            requests_auth = None

        if request is None:
            factory = RequestFactory()
            self.request = factory.get('/')
        else:
            self.request = request

        self.xqueue_interface = XQueueInterface(
            settings.XQUEUE_INTERFACE['url'],
            settings.XQUEUE_INTERFACE['django_auth'],
            requests_auth,
        )
        self.whitelist = CertificateWhitelist.objects.all()
        self.restricted = UserProfile.objects.filter(allow_certificate=False)
        self.use_https = True

    def regen_cert(
            self,
            student,
            course_id,
            course=None,
            designation=None,
            forced_grade=None,
            template_file=None,
            generate_pdf=True,
    ):
        """(Re-)Make certificate for a particular student in a particular course

        Arguments:
          student   - User.object
          course_id - courseenrollment.course_id (string)

        WARNING: this command will leave the old certificate, if one exists,
                 laying around in AWS taking up space. If this is a problem,
                 take pains to clean up storage before running this command.

        Change the certificate status to unavailable (if it exists) and request
        grading. Passing grades will put a certificate request on the queue.

        Return the status object.
        """
        # TODO: when del_cert is implemented and plumbed through certificates
        #       repo also, do a deletion followed by a creation r/t a simple
        #       recreation. XXX: this leaves orphan cert files laying around in
        #       AWS. See note in the docstring too.
        try:
            certificate = GeneratedCertificate.objects.get(user=student, course_id=course_id)

            LOGGER.info(
                (
                    u"Found an existing certificate entry for student %s "
                    u"in course '%s' "
                    u"with status '%s' while regenerating certificates. "
                ),
                student.id,
                unicode(course_id),
                certificate.status
            )

            certificate.status = status.unavailable
            certificate.save()

            LOGGER.info(
                (
                    u"The certificate status for student %s "
                    u"in course '%s' has been changed to '%s'."
                ),
                student.id,
                unicode(course_id),
                certificate.status
            )

        except GeneratedCertificate.DoesNotExist:
            pass

        return self.add_cert(
            student,
            course_id,
            course=course,
            designation=designation,
            forced_grade=forced_grade,
            template_file=template_file,
            generate_pdf=generate_pdf
        )

    def del_cert(self, student, course_id):

        """
        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Removes certificate for a student, will change
        the certificate status to 'deleting'.

        Certificate must be in the 'error' or 'downloadable' state
        otherwise it will return the current state

        """

        raise NotImplementedError

    # pylint: disable=too-many-statements
    def add_cert(self, student, course_id, course=None, forced_grade=None, template_file=None,
                 designation=None, generate_pdf=True):
        """
        Request a new certificate for a student.

        Arguments:
          student   - User.object
          course_id - courseenrollment.course_id (CourseKey)
          forced_grade - a string indicating a grade parameter to pass with
                         the certificate request. If this is given, grading
                         will be skipped.
          generate_pdf - Boolean should a message be sent in queue to generate certificate PDF

        Will change the certificate status to 'generating' or
        `downloadable` in case of web view certificates.

        Certificate must be in the 'unavailable', 'error',
        'deleted' or 'generating' state.

        If a student has a passing grade or is in the whitelist
        table for the course a request will be made for a new cert.

        If a student has allow_certificate set to False in the
        userprofile table the status will change to 'restricted'

        If a student does not have a passing grade the status
        will change to status.notpassing

        Returns the student's status and newly created certificate instance
        """

        valid_statuses = [
            status.generating,
            status.unavailable,
            status.deleted,
            status.error,
            status.notpassing,
            status.downloadable
        ]

        cert_status = certificate_status_for_student(student, course_id)['status']
        new_status = cert_status
        cert = None

        if cert_status not in valid_statuses:
            LOGGER.warning(
                (
                    u"Cannot create certificate generation task for user %s "
                    u"in the course '%s'; "
                    u"the certificate status '%s' is not one of %s."
                ),
                student.id,
                unicode(course_id),
                cert_status,
                unicode(valid_statuses)
            )
        else:
            # grade the student

            # re-use the course passed in optionally so we don't have to re-fetch everything
            # for every student
            if course is None:
                course = modulestore().get_course(course_id, depth=0)
            profile = UserProfile.objects.get(user=student)
            profile_name = profile.name

            # Needed
            self.request.user = student
            self.request.session = {}

            course_name = course.display_name or unicode(course_id)
            is_whitelisted = self.whitelist.filter(user=student, course_id=course_id, whitelist=True).exists()
            grade = grades.grade(student, self.request, course)
            enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(student, course_id)
            mode_is_verified = enrollment_mode in GeneratedCertificate.VERIFIED_CERTS_MODES
            user_is_verified = SoftwareSecurePhotoVerification.user_is_verified(student)
            cert_mode = enrollment_mode

            # For credit mode generate verified certificate
            if cert_mode == CourseMode.CREDIT_MODE:
                cert_mode = CourseMode.VERIFIED

            if mode_is_verified and user_is_verified:
                template_pdf = "certificate-template-{id.org}-{id.course}-verified.pdf".format(id=course_id)
            elif mode_is_verified and not user_is_verified:
                template_pdf = "certificate-template-{id.org}-{id.course}.pdf".format(id=course_id)
                cert_mode = GeneratedCertificate.MODES.honor
            else:
                # honor code and audit students
                template_pdf = "certificate-template-{id.org}-{id.course}.pdf".format(id=course_id)
            if forced_grade:
                grade['grade'] = forced_grade

            cert, __ = GeneratedCertificate.objects.get_or_create(user=student, course_id=course_id)

            cert.mode = cert_mode
            cert.user = student
            cert.grade = grade['percent']
            cert.course_id = course_id
            cert.name = profile_name
            cert.download_url = ''
            # Strip HTML from grade range label
            grade_contents = grade.get('grade', None)
            try:
                grade_contents = lxml.html.fromstring(grade_contents).text_content()
            except (TypeError, XMLSyntaxError, ParserError) as exc:
                LOGGER.info(
                    (
                        u"Could not retrieve grade for student %s "
                        u"in the course '%s' "
                        u"because an exception occurred while parsing the "
                        u"grade contents '%s' as HTML. "
                        u"The exception was: '%s'"
                    ),
                    student.id,
                    unicode(course_id),
                    grade_contents,
                    unicode(exc)
                )

                #   Despite blowing up the xml parser, bad values here are fine
                grade_contents = None

            if is_whitelisted or grade_contents is not None:

                if is_whitelisted:
                    LOGGER.info(
                        u"Student %s is whitelisted in '%s'",
                        student.id,
                        unicode(course_id)
                    )

                # check to see whether the student is on the
                # the embargoed country restricted list
                # otherwise, put a new certificate request
                # on the queue

                if self.restricted.filter(user=student).exists():
                    new_status = status.restricted
                    cert.status = new_status
                    cert.save()

                    LOGGER.info(
                        (
                            u"Student %s is in the embargoed country restricted "
                            u"list, so their certificate status has been set to '%s' "
                            u"for the course '%s'. "
                            u"No certificate generation task was sent to the XQueue."
                        ),
                        student.id,
                        new_status,
                        unicode(course_id)
                    )
                else:
                    key = make_hashkey(random.random())
                    cert.key = key
                    contents = {
                        'action': 'create',
                        'username': student.username,
                        'course_id': unicode(course_id),
                        'course_name': course_name,
                        'name': profile_name,
                        'grade': grade_contents,
                        'template_pdf': template_pdf,
                        'designation': designation,
                    }
                    if template_file:
                        contents['template_pdf'] = template_file
                    if generate_pdf:
                        new_status = status.generating
                    else:
                        new_status = status.downloadable
                        cert.verify_uuid = uuid4().hex

                    cert.status = new_status
                    cert.save()

                    if generate_pdf:
                        try:
                            self._send_to_xqueue(contents, key)
                        except XQueueAddToQueueError as exc:
                            new_status = ExampleCertificate.STATUS_ERROR
                            cert.status = new_status
                            cert.error_reason = unicode(exc)
                            cert.save()
                            LOGGER.critical(
                                (
                                    u"Could not add certificate task to XQueue.  "
                                    u"The course was '%s' and the student was '%s'."
                                    u"The certificate task status has been marked as 'error' "
                                    u"and can be re-submitted with a management command."
                                ), course_id, student.id
                            )
                        else:
                            LOGGER.info(
                                (
                                    u"The certificate status has been set to '%s'.  "
                                    u"Sent a certificate grading task to the XQueue "
                                    u"with the key '%s'. "
                                ),
                                new_status,
                                key
                            )
            else:
                new_status = status.notpassing
                cert.status = new_status
                cert.save()

                LOGGER.info(
                    (
                        u"Student %s does not have a grade for '%s', "
                        u"so their certificate status has been set to '%s'. "
                        u"No certificate generation task was sent to the XQueue."
                    ),
                    student.id,
                    unicode(course_id),
                    new_status
                )

        return new_status, cert

    def add_example_cert(self, example_cert):
        """Add a task to create an example certificate.

        Unlike other certificates, an example certificate is
        not associated with any particular user and is never
        shown to students.

        If an error occurs when adding the example certificate
        to the queue, the example certificate status
        will be set to "error".

        Arguments:
            example_cert (ExampleCertificate)

        """
        contents = {
            'action': 'create',
            'course_id': unicode(example_cert.course_key),
            'name': example_cert.full_name,
            'template_pdf': example_cert.template,

            # Example certificates are not associated with a particular user.
            # However, we still need to find the example certificate when
            # we receive a response from the queue.  For this reason,
            # we use the example certificate's unique identifier as a username.
            # Note that the username is *not* displayed on the certificate;
            # it is used only to identify the certificate task in the queue.
            'username': example_cert.uuid,

            # We send this extra parameter to differentiate
            # example certificates from other certificates.
            # This is not used by the certificates workers or XQueue.
            'example_certificate': True,
        }

        # The callback for example certificates is different than the callback
        # for other certificates.  Although both tasks use the same queue,
        # we can distinguish whether the certificate was an example cert based
        # on which end-point XQueue uses once the task completes.
        callback_url_path = reverse('certificates.views.update_example_certificate')

        try:
            self._send_to_xqueue(
                contents,
                example_cert.access_key,
                task_identifier=example_cert.uuid,
                callback_url_path=callback_url_path
            )
            LOGGER.info(u"Started generating example certificates for course '%s'.", example_cert.course_key)
        except XQueueAddToQueueError as exc:
            example_cert.update_status(
                ExampleCertificate.STATUS_ERROR,
                error_reason=unicode(exc)
            )
            LOGGER.critical(
                (
                    u"Could not add example certificate with uuid '%s' to XQueue.  "
                    u"The exception was %s.  "
                    u"The example certificate has been marked with status 'error'."
                ), example_cert.uuid, unicode(exc)
            )

    def _send_to_xqueue(self, contents, key, task_identifier=None, callback_url_path='/update_certificate'):
        """Create a new task on the XQueue.

        Arguments:
            contents (dict): The contents of the XQueue task.
            key (str): An access key for the task.  This will be sent
                to the callback end-point once the task completes,
                so that we can validate that the sender is the same
                entity that received the task.

        Keyword Arguments:
            callback_url_path (str): The path of the callback URL.
                If not provided, use the default end-point for student-generated
                certificates.

        """
        callback_url = u'{protocol}://{base_url}{path}'.format(
            protocol=("https" if self.use_https else "http"),
            base_url=settings.SITE_NAME,
            path=callback_url_path
        )

        # Append the key to the URL
        # This is necessary because XQueue assumes that only one
        # submission is active for a particular URL.
        # If it receives a second submission with the same callback URL,
        # it "retires" any other submission with the same URL.
        # This was a hack that depended on the URL containing the user ID
        # and courseware location; an assumption that does not apply
        # to certificate generation.
        # XQueue also truncates the callback URL to 128 characters,
        # but since our key lengths are shorter than that, this should
        # not affect us.
        callback_url += "?key={key}".format(
            key=(
                task_identifier
                if task_identifier is not None
                else key
            )
        )

        xheader = make_xheader(callback_url, key, settings.CERT_QUEUE)

        (error, msg) = self.xqueue_interface.send_to_queue(
            header=xheader, body=json.dumps(contents))
        if error:
            exc = XQueueAddToQueueError(error, msg)
            LOGGER.critical(unicode(exc))
            raise exc
