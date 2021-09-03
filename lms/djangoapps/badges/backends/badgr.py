"""
Badge Awarding backend for Badgr-Server.
"""


import base64
import datetime
import json
import hashlib
import logging
import mimetypes

import requests
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from eventtracking import tracker
from lazy import lazy  # lint-amnesty, pylint: disable=no-name-in-module
from requests.packages.urllib3.exceptions import HTTPError  # lint-amnesty, pylint: disable=import-error

from edx_django_utils.cache import TieredCache

from lms.djangoapps.badges.backends.base import BadgeBackend
from lms.djangoapps.badges.models import BadgeAssertion

MAX_SLUG_LENGTH = 255
LOGGER = logging.getLogger(__name__)


class BadgrBackend(BadgeBackend):
    """
    Backend for Badgr-Server by Concentric Sky. http://info.badgr.io/
    """
    badges = []

    def __init__(self):
        super().__init__()
        if None in (settings.BADGR_USERNAME,
                    settings.BADGR_PASSWORD,
                    settings.BADGR_TOKENS_CACHE_KEY,
                    settings.BADGR_ISSUER_SLUG,
                    settings.BADGR_BASE_URL):
            error_msg = (
                "One or more of the required settings are not defined. "
                "Required settings: BADGR_USERNAME, BADGR_PASSWORD, "
                "BADGR_TOKENS_CACHE_KEY, BADGR_ISSUER_SLUG, BADGR_BASE_URL.")
            LOGGER.error(error_msg)
            raise ImproperlyConfigured(error_msg)

    @lazy
    def _base_url(self):
        """
        Base URL for API requests that contain the issuer slug.
        """
        return f"{settings.BADGR_BASE_URL}/v2/issuers/{settings.BADGR_ISSUER_SLUG}"

    @lazy
    def _badge_create_url(self):
        """
        URL for generating a new Badge specification
        """
        return f"{self._base_url}/badgeclasses"

    def _badge_url(self, slug):
        """
        Get the URL for a course's badge in a given mode.
        """
        return f"{settings.BADGR_BASE_URL}/v2/badgeclasses/{slug}"

    def _assertion_url(self, slug):
        """
        URL for generating a new assertion.
        """
        return f"{self._badge_url(slug)}/assertions"

    def _slugify(self, badge_class):
        """
        Get a compatible badge slug from the specification.
        """
        slug = badge_class.issuing_component + badge_class.slug
        if badge_class.issuing_component and badge_class.course_id:
            # Make this unique to the course, and down to 64 characters.
            # We don't do this to badges without issuing_component set for backwards compatibility.
            slug = hashlib.sha256((slug + str(badge_class.course_id)).encode('utf-8')).hexdigest()
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
                "Encountered an error when contacting the Badgr-Server. Request sent to %r with headers %r.\n"
                "and data values %r\n"
                "Response status was %s.\n%s",
                response.request.url, response.request.headers,
                data,
                response.status_code, response.content
            )
            raise

    def _create_badge(self, badge_class):
        """
        Create the badge class on Badgr.
        """
        image = badge_class.image
        # We don't want to bother validating the file any further than making sure we can detect its MIME type,
        # for HTTP. The Badgr-Server should tell us if there's anything in particular wrong with it.
        content_type, __ = mimetypes.guess_type(image.name)
        if not content_type:
            raise ValueError(
                "Could not determine content-type of image! Make sure it is a properly named .png file. "
                "Filename was: {}".format(image.name)
            )
        with open(image.path, 'rb') as image_file:
            files = {'image': (image.name, image_file, content_type)}
            data = {
                'name': badge_class.display_name,
                'criteriaUrl': badge_class.criteria,
                'description': badge_class.description,
            }
            result = requests.post(
                self._badge_create_url, headers=self._get_headers(),
                data=data, files=files, timeout=settings.BADGR_TIMEOUT)
            self._log_if_raised(result, data)
            try:
                result_json = result.json()
                badgr_badge_class = result_json['result'][0]
                badgr_server_slug = badgr_badge_class.get('entityId')
                badge_class.badgr_server_slug = badgr_server_slug
                badge_class.save()
            except Exception as excep:  # pylint: disable=broad-except
                LOGGER.error(
                    'Error on saving Badgr Server Slug of badge_class slug '
                    '"{0}" with response json "{1}" : {2}'.format(
                        badge_class.slug, result.json(), excep))

    def _send_assertion_created_event(self, user, assertion):
        """
        Send an analytics event to record the creation of a badge assertion.
        """
        tracker.emit(
            'edx.badge.assertion.created', {
                'user_id': user.id,
                'badge_slug': assertion.badge_class.slug,
                'badge_badgr_server_slug': assertion.badge_class.badgr_server_slug,
                'badge_name': assertion.badge_class.display_name,
                'issuing_component': assertion.badge_class.issuing_component,
                'course_id': str(assertion.badge_class.course_id),
                'enrollment_mode': assertion.badge_class.mode,
                'assertion_id': assertion.id,
                'assertion_image_url': assertion.image_url,
                'assertion_json_url': assertion.assertion_url,
                'issuer': assertion.data.get('issuer'),
            }
        )

    def _create_assertion(self, badge_class, user, evidence_url):
        """
        Register an assertion with the Badgr server for a particular user for a specific class.
        """
        data = {
            "recipient": {
                "identity": user.email,
                "type": "email"
            },
            "evidence": [
                {
                    "url": evidence_url
                }
            ],
            "notify": settings.BADGR_ENABLE_NOTIFICATIONS,
        }
        response = requests.post(
            self._assertion_url(badge_class.badgr_server_slug),
            headers=self._get_headers(),
            json=data,
            timeout=settings.BADGR_TIMEOUT
        )
        self._log_if_raised(response, data)
        assertion, __ = BadgeAssertion.objects.get_or_create(user=user, badge_class=badge_class)
        try:
            response_json = response.json()
            assertion.data = response_json['result'][0]
            assertion.image_url = assertion.data['image']
            assertion.assertion_url = assertion.data['openBadgeId']
            assertion.backend = 'BadgrBackend'
            assertion.save()
            self._send_assertion_created_event(user, assertion)
            return assertion

        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error(
                'Error saving BadgeAssertion for user: "{0}" '
                'with response from server: {1};'
                'Encountered exception: {2}'.format(
                    user.email, response.text, exc))

    @staticmethod
    def _fernet_setup():
        """
        Set up the Fernet class for encrypting/decrypting tokens.
        Fernet keys must always be URL-safe base64 encoded 32-byte binary
        strings. Use the SECRET_KEY for creating the encryption key.
        """
        fernet_key = base64.urlsafe_b64encode(
            settings.SECRET_KEY.ljust(64).encode('utf-8')[:32]
        )
        return Fernet(fernet_key)

    def _encrypt_token(self, token):
        """
        Encrypt a token
        """
        fernet = self._fernet_setup()
        return fernet.encrypt(token.encode('utf-8'))

    def _decrypt_token(self, token):
        """
        Decrypt a token
        """
        fernet = self._fernet_setup()
        return fernet.decrypt(token).decode()

    def _get_and_cache_oauth_tokens(self, refresh_token=None):
        """
        Get or renew OAuth tokens. If a refresh_token is provided,
        use it to renew tokens, otherwise create new ones.
        Once tokens are created/renewed, encrypt the values and cache them.
        """
        data = {
            'username': settings.BADGR_USERNAME,
            'password': settings.BADGR_PASSWORD,
        }
        if refresh_token:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }

        oauth_url = "{}/o/token".format(settings.BADGR_BASE_URL)

        response = requests.post(
            oauth_url, data=data, timeout=settings.BADGR_TIMEOUT
        )
        self._log_if_raised(response, data)
        try:
            data = response.json()
            result = {
                'access_token': self._encrypt_token(data['access_token']),
                'refresh_token': self._encrypt_token(data['refresh_token']),
                'expires_at': datetime.datetime.utcnow() + datetime.timedelta(
                    seconds=data['expires_in'])
            }
            # The refresh_token is long-lived, we want to be able to retrieve
            # it from cache as long as possible.
            # Set the cache timeout to None so the cache key never expires
            # (https://docs.djangoproject.com/en/2.2/topics/cache/#cache-arguments)
            TieredCache.set_all_tiers(
                settings.BADGR_TOKENS_CACHE_KEY, result, None)
            return result
        except (KeyError, json.decoder.JSONDecodeError) as json_error:
            raise requests.RequestException(response=response) from json_error

    def _get_access_token(self):
        """
        Get an access token from cache if one is present and valid. If a
        token is cached but expired, renew it. If all fails or a token has
        not yet been cached, create a new one.
        """
        tokens = {}
        cached_response = TieredCache.get_cached_response(
            settings.BADGR_TOKENS_CACHE_KEY)
        if cached_response.is_found:
            cached_tokens = cached_response.value
            # add a 5 seconds buffer to the cutoff timestamp to make sure
            # the token will not expire while in use
            expiry_cutoff = (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
            if cached_tokens.get('expires_at') > expiry_cutoff:
                tokens = cached_tokens
            else:
                # renew the tokens with the cached `refresh_token`
                refresh_token = self._decrypt_token(cached_tokens.get(
                    'refresh_token'))
                tokens = self._get_and_cache_oauth_tokens(
                    refresh_token=refresh_token)

        # if no tokens are cached or something went wrong with
        # retreiving/renewing them, go and create new tokens
        if not tokens:
            tokens = self._get_and_cache_oauth_tokens()
        return self._decrypt_token(tokens.get('access_token'))

    def _get_headers(self):
        """
        Headers to send along with the request-- used for authentication.
        """
        access_token = self._get_access_token()
        return {'Authorization': 'Bearer {}'.format(access_token)}

    def _ensure_badge_created(self, badge_class):
        """
        Verify a badge has been created for this badge class, and create it if not.
        """
        slug = badge_class.badgr_server_slug
        if slug in BadgrBackend.badges:
            return
        response = requests.get(self._badge_url(slug), headers=self._get_headers(), timeout=settings.BADGR_TIMEOUT)
        if response.status_code != 200:
            self._create_badge(badge_class)
        BadgrBackend.badges.append(slug)

    def award(self, badge_class, user, evidence_url=None):
        """
        Make sure the badge class has been created on the backend, and then award the badge class to the user.
        """
        self._ensure_badge_created(badge_class)
        return self._create_assertion(badge_class, user, evidence_url)
