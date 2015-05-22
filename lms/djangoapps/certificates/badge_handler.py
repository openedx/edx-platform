"""
BadgeHandler object-- used to award Badges to users who have completed courses.
"""
import hashlib
import logging
import mimetypes
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
import requests

from django.conf import settings
from django.core.urlresolvers import reverse
from lazy import lazy
from requests.packages.urllib3.exceptions import HTTPError
from certificates.models import BadgeAssertion, BadgeImageConfiguration
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

LOGGER = logging.getLogger(__name__)


class BadgeHandler(object):
    """
    The only properly public method of this class is 'award'. If an alternative object is created for a different
    badging service, the other methods don't need to be reproduced.
    """
    # Global caching dict
    badges = {}

    def __init__(self, course_key):
        self.course_key = course_key
        assert settings.BADGR_API_TOKEN

    @lazy
    def base_url(self):
        """
        Base URL for all API requests.
        """
        return "{}/v1/issuer/issuers/{}".format(settings.BADGR_BASE_URL, settings.BADGR_ISSUER_SLUG)

    @lazy
    def badge_create_url(self):
        """
        URL for generating a new Badge specification
        """
        return "{}/badges".format(self.base_url)

    def badge_url(self, mode):
        """
        Get the URL for a course's badge in a given mode.
        """
        return "{}/{}".format(self.badge_create_url, self.course_slug(mode))

    def assertion_url(self, mode):
        """
        URL for generating a new assertion.
        """
        return "{}/assertions".format(self.badge_url(mode))

    def course_slug(self, mode):
        """
        Slug ought to be deterministic and limited in size so it's not too big for Badgr.

        Badgr's max slug length is 255.
        """
        # Seven digits should be enough to realistically avoid collisions. That's what git services use.
        digest = hashlib.sha256(u"{}{}".format(unicode(self.course_key), unicode(mode))).hexdigest()[:7]
        base_slug = slugify(unicode(self.course_key) + u'_{}_'.format(mode))[:248]
        return base_slug + digest

    def log_if_raised(self, response, data):
        """
        Log server response if there was an error.
        """
        try:
            response.raise_for_status()
        except HTTPError:
            LOGGER.error(
                u"Encountered an error when contacting the Badgr-Server. Request sent to %s with headers %s.\n"
                u"and data values %s\n"
                u"Response status was %s.\n%s",
                repr(response.request.url), repr(response.request.headers),
                repr(data),
                response.status_code, response.body
            )
            raise

    def get_headers(self):
        """
        Headers to send along with the request-- used for authentication.
        """
        return {'Authorization': 'Token {}'.format(settings.BADGR_API_TOKEN)}

    def ensure_badge_created(self, mode):
        """
        Verify a badge has been created for this mode of the course, and, if not, create it
        """
        if self.course_slug(mode) in BadgeHandler.badges:
            return
        response = requests.get(self.badge_url(mode), headers=self.get_headers())
        if response.status_code != 200:
            self.create_badge(mode)
        BadgeHandler.badges[self.course_slug(mode)] = True

    @staticmethod
    def badge_name_field(course, mode):
        """
        Get the name for the badge, based on the course name. Max size is 255.
        """
        return _(u"{course_display_name} ({course_mode})").format(
            course_display_name=course.display_name,
            # Course modes may be translated, but this whole string won't be available for translation.
            # pylint: disable=translation-of-non-string
            course_mode=_(mode),
        )[:255]

    @staticmethod
    def badge_description(course):
        """
        Returns the badge
        """
        if course.end:
            return _(u"{start_date} to {end_date}").format(
                start_date=course.start.date(),
                end_date=course.end.date(),
            )
        else:
            return u"{start_date}".format(start_date=course.start.date())

    def create_badge(self, mode):
        """
        Create the badge spec for a course's mode.
        """
        course = modulestore().get_course(self.course_key)
        image = BadgeImageConfiguration.image_for_mode(mode)
        # We don't want to bother validating the file any further than making sure we can detect its MIME type,
        # for HTTP. The Badgr-Server should tell us if there's anything in particular wrong with it.
        content_type, __ = mimetypes.guess_type(image.name)
        if not content_type:
            raise ValueError(
                "Could not determine content-type of image! Make sure it is a properly named .png file."
            )
        files = {'image': (image.name, image, content_type)}
        about_path = reverse('about_course', kwargs={'course_id': unicode(self.course_key)})
        scheme = u"https" if settings.HTTPS == "on" else u"http"
        data = {
            'name': self.badge_name_field(course, mode),
            'criteria': u'{}://{}{}'.format(scheme, settings.SITE_NAME, about_path),
            'slug': self.course_slug(mode),
            'description': self.badge_description(course)
        }
        result = requests.post(self.badge_create_url, headers=self.get_headers(), data=data, files=files)
        self.log_if_raised(result, data)

    def create_assertion(self, user, mode):
        """
        Register an assertion with the Badgr server for a particular user in a particular course mode for
        this course.
        """
        data = {'email': user.email}
        response = requests.post(self.assertion_url(mode), headers=self.get_headers(), data=data)
        self.log_if_raised(response, data)
        assertion, __ = BadgeAssertion.objects.get_or_create(course_id=self.course_key, user=user)
        assertion.data = response.json()
        assertion.save()

    def award(self, user):
        """
        Award a user a badge for their work on the course.
        """
        mode = CourseEnrollment.objects.get(user=user, course_id=self.course_key).mode
        self.ensure_badge_created(mode)
        self.create_assertion(user, mode)
