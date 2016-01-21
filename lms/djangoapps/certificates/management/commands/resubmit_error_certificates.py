"""Management command for re-submitting certificates with an error status.

Certificates may have "error" status for a variety of reasons,
but the most likely is that the course was misconfigured
in the certificates worker.

This management command identifies certificate tasks
that have an error status and re-resubmits them.

Example usage:

    # Re-submit certificates for *all* courses
    $ ./manage.py lms resubmit_error_certificates

    # Re-submit certificates for particular courses
    $ ./manage.py lms resubmit_error_certificates -c edX/DemoX/Fall_2015 -c edX/DemoX/Spring_2016

"""
import logging
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from certificates import api as certs_api
from certificates.models import GeneratedCertificate, CertificateStatuses


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Resubmit certificates with error status. """

    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--course',
            metavar='COURSE_KEY',
            dest='course_key_list',
            action='append',
            default=[],
            help='Only re-submit certificates for these courses.'
        ),
    )

    def handle(self, *args, **options):
        """Resubmit certificates with status 'error'.

        Arguments:
            username (unicode): Identifier for the certificate's user.

        Keyword Arguments:
            course_key_list (list): List of course key strings.

        Raises:
            CommandError

        """
        only_course_keys = []
        for course_key_str in options.get('course_key_list', []):
            try:
                only_course_keys.append(CourseKey.from_string(course_key_str))
            except InvalidKeyError:
                raise CommandError(
                    '"{course_key_str}" is not a valid course key.'.format(
                        course_key_str=course_key_str
                    )
                )

        if only_course_keys:
            LOGGER.info(
                (
                    u'Starting to re-submit certificates with status "error" '
                    u'in these courses: %s'
                ), ", ".join([unicode(key) for key in only_course_keys])
            )
        else:
            LOGGER.info(u'Starting to re-submit certificates with status "error".')

        # Retrieve the IDs of generated certificates with
        # error status in the set of courses we're considering.
        queryset = (
            GeneratedCertificate.objects.select_related('user')  # pylint: disable=no-member
        ).filter(status=CertificateStatuses.error)
        if only_course_keys:
            queryset = queryset.filter(course_id__in=only_course_keys)

        resubmit_list = [(cert.user, cert.course_id) for cert in queryset]
        course_cache = {}
        resubmit_count = 0
        for user, course_key in resubmit_list:
            course = self._load_course_with_cache(course_key, course_cache)

            if course is not None:
                certs_api.generate_user_certificates(user, course_key, course=course)
                resubmit_count += 1
                LOGGER.info(
                    (
                        u"Re-submitted certificate for user %s "
                        u"in course '%s'"
                    ), user.id, course_key
                )
            else:
                LOGGER.error(
                    (
                        u"Could not find course for course key '%s'.  "
                        u"Certificate for user %s will not be resubmitted."
                    ), course_key, user.id
                )

        LOGGER.info("Finished resubmitting %s certificate tasks", resubmit_count)

    def _load_course_with_cache(self, course_key, course_cache):
        """Retrieve the course, then cache it to avoid Mongo queries. """
        course = (
            course_cache[course_key] if course_key in course_cache
            else modulestore().get_course(course_key, depth=0)
        )
        course_cache[course_key] = course
        return course
