"""
Badge Awarding backend for Badgr-Server.
"""
import hashlib
import logging
import mimetypes

import requests
from django.conf import settings
from lazy import lazy
from requests.packages.urllib3.exceptions import HTTPError

from badges.backends.base import BadgeBackend
from eventtracking import tracker

from badges.models import BadgeAssertion

MAX_SLUG_LENGTH = 255
LOGGER = logging.getLogger(__name__)


class BadgrBackend(BadgeBackend):
    """
    Backend for Badgr-Server by Concentric Sky. http://info.badgr.io/
    """
    badges = []

    def __init__(self):
        assert settings.BADGR_API_TOKEN

    @lazy
    def _base_url(self):
        """
        Base URL for all API requests.
        """
        return "{}/v1/issuer/issuers/{}".format(settings.BADGR_BASE_URL, settings.BADGR_ISSUER_SLUG)

    @lazy
    def _badge_create_url(self):
        """
        URL for generating a new Badge specification
        """
        return "{}/badges".format(self._base_url)

    def _badge_url(self, slug):
        """
        Get the URL for a course's badge in a given mode.
        """
        return "{}/{}".format(self._badge_create_url, slug)

    def _assertion_url(self, slug):
        """
        URL for generating a new assertion.
        """
        return "{}/assertions".format(self._badge_url(slug))

    def _slugify(self, badge_class):
        """
        Get a compatible badge slug from the specification.
        """
        slug = badge_class.issuing_component + badge_class.slug
        if len(slug) > MAX_SLUG_LENGTH:
            # Will be 64 characters.
            slug = hashlib.sha256(slug).hexdigest()
        return slug

    def _log_if_raised(self, response, data):
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
                response.status_code, response.content
            )
            raise

    def _create_badge(self, badge_class):
        """
        Create the badge spec for a course's mode.
        """
        image = badge_class.image
        # We don't want to bother validating the file any further than making sure we can detect its MIME type,
        # for HTTP. The Badgr-Server should tell us if there's anything in particular wrong with it.
        content_type, __ = mimetypes.guess_type(image.name)
        if not content_type:
            raise ValueError(
                "Could not determine content-type of image! Make sure it is a properly named .png file."
            )
        files = {'image': (image.name, image, content_type)}
        data = {
            'name': badge_class.display_name,
            'criteria': badge_class.criteria,
            'slug': self._slugify(badge_class),
            'description': badge_class.description,
        }
        result = requests.post(self._badge_create_url, headers=self._get_headers(), data=data, files=files)
        self._log_if_raised(result, data)

    def send_assertion_created_event(self, user, assertion):
        """
        Send an analytics event to record the creation of a badge assertion.
        """
        tracker.emit(
            'edx.badge.assertion.created', {
                'user_id': user.id,
                'course_id': unicode(assertion.badge_class.course_id),
                'enrollment_mode': assertion.badge_class.mode,
                'assertion_id': assertion.id,
                'assertion_image_url': assertion.image_url,
                'assertion_json_url': assertion.assertion_url,
                'issuer': assertion.data['issuer'],
            }
        )

    def _create_assertion(self, badge_class, user, evidence_url):
        """
        Register an assertion with the Badgr server for a particular user in a particular course mode for
        this course.
        """
        data = {
            'email': user.email,
            'evidence': evidence_url,
        }
        response = requests.post(
            self._assertion_url(self._slugify(badge_class)), headers=self._get_headers(), data=data
        )
        self._log_if_raised(response, data)
        assertion, __ = BadgeAssertion.objects.get_or_create(user=user, badge_class=badge_class)
        assertion.data = response.json()
        assertion.backend = 'BadgrBackend'
        assertion.image_url = assertion.data['image']
        assertion.assertion_url = assertion.data['json']['id']
        assertion.save()
        self.send_assertion_created_event(user, assertion)
        return assertion

    @staticmethod
    def _get_headers():
        """
        Headers to send along with the request-- used for authentication.
        """
        return {'Authorization': 'Token {}'.format(settings.BADGR_API_TOKEN)}

    def _ensure_badge_created(self, badge_class):
        """
        Verify a badge has been created for this mode of the course, and, if not, create it
        """
        slug = self._slugify(badge_class)
        if slug in BadgrBackend.badges:
            return
        response = requests.get(self._badge_url(slug), headers=self._get_headers())
        if response.status_code != 200:
            self._create_badge(badge_class)
        BadgrBackend.badges.append(slug)

    def award(self, badge_class, user, evidence_url=None):
        self._ensure_badge_created(badge_class)
        return self._create_assertion(badge_class, user, evidence_url)
