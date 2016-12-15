"""
Middleware to serve assets.
"""

import logging

import datetime
from django.http import (
    HttpResponse, HttpResponseNotModified, HttpResponseForbidden,
    HttpResponseBadRequest, HttpResponseNotFound)
from student.models import CourseEnrollment
from contentserver.models import CourseAssetCacheTtlConfig

from clean_headers import remove_headers_from_response
from xmodule.assetstore.assetmgr import AssetManager
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from xmodule.modulestore import InvalidLocationError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import AssetLocator
from cache_toolbox.core import get_cached_content, set_cached_content
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import NotFoundError

# TODO: Soon as we have a reasonable way to serialize/deserialize AssetKeys, we need
# to change this file so instead of using course_id_partial, we're just using asset keys

log = logging.getLogger(__name__)
HTTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


class StaticContentServer(object):
    def is_asset_request(self, request):
        """Determines whether the given request is an asset request"""
        return (
            request.path.startswith('/' + XASSET_LOCATION_TAG + '/')
            or
            request.path.startswith('/' + AssetLocator.CANONICAL_NAMESPACE)
        )

    def process_request(self, request):
        """Process the given request"""
        if self.is_asset_request(request):
            # Make sure we can convert this request into a location.
            if AssetLocator.CANONICAL_NAMESPACE in request.path:
                request.path = request.path.replace('block/', 'block@', 1)
            try:
                loc = StaticContent.get_location_from_path(request.path)
            except (InvalidLocationError, InvalidKeyError):
                return HttpResponseBadRequest()

            # Try and load the asset.
            content = None
            try:
                content = self.load_asset_from_location(loc)
            except (ItemNotFoundError, NotFoundError):
                return HttpResponseNotFound()

            # Check that user has access to the content.
            if not self.is_user_authorized(request, content, loc):
                return HttpResponseForbidden('Unauthorized')

            # Figure out if the client sent us a conditional request, and let them know
            # if this asset has changed since then.
            last_modified_at_str = content.last_modified_at.strftime(HTTP_DATE_FORMAT)
            if 'HTTP_IF_MODIFIED_SINCE' in request.META:
                if_modified_since = request.META['HTTP_IF_MODIFIED_SINCE']
                if if_modified_since == last_modified_at_str:
                    return HttpResponseNotModified()

            # *** File streaming within a byte range ***
            # If a Range is provided, parse Range attribute of the request
            # Add Content-Range in the response if Range is structurally correct
            # Request -> Range attribute structure: "Range: bytes=first-[last]"
            # Response -> Content-Range attribute structure: "Content-Range: bytes first-last/totalLength"
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.35
            response = None
            if request.META.get('HTTP_RANGE'):
                # If we have a StaticContent, get a StaticContentStream.  Can't manipulate the bytes otherwise.
                if type(content) == StaticContent:
                    content = AssetManager.find(loc, as_stream=True)

                header_value = request.META['HTTP_RANGE']
                try:
                    unit, ranges = parse_range_header(header_value, content.length)
                except ValueError as exception:
                    # If the header field is syntactically invalid it should be ignored.
                    log.exception(
                        u"%s in Range header: %s for content: %s", exception.message, header_value, unicode(loc)
                    )
                else:
                    if unit != 'bytes':
                        # Only accept ranges in bytes
                        log.warning(u"Unknown unit in Range header: %s for content: %s", header_value, unicode(loc))
                    elif len(ranges) > 1:
                        # According to Http/1.1 spec content for multiple ranges should be sent as a multipart message.
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.16
                        # But we send back the full content.
                        log.warning(
                            u"More than 1 ranges in Range header: %s for content: %s", header_value, unicode(loc)
                        )
                    else:
                        first, last = ranges[0]

                        if 0 <= first <= last < content.length:
                            # If the byte range is satisfiable
                            response = HttpResponse(content.stream_data_in_range(first, last))
                            response['Content-Range'] = 'bytes {first}-{last}/{length}'.format(
                                first=first, last=last, length=content.length
                            )
                            response['Content-Length'] = str(last - first + 1)
                            response.status_code = 206  # Partial Content
                        else:
                            log.warning(
                                u"Cannot satisfy ranges in Range header: %s for content: %s", header_value, unicode(loc)
                            )
                            return HttpResponse(status=416)  # Requested Range Not Satisfiable

            # If Range header is absent or syntactically invalid return a full content response.
            if response is None:
                response = HttpResponse(content.stream_data())
                response['Content-Length'] = content.length

            # "Accept-Ranges: bytes" tells the user that only "bytes" ranges are allowed
            response['Accept-Ranges'] = 'bytes'
            response['Content-Type'] = content.content_type

            # Set any caching headers, and do any response cleanup needed.  Based on how much
            # middleware we have in place, there's no easy way to use the built-in Django
            # utilities and properly sanitize and modify a response to ensure that it is as
            # cacheable as possible, which is why we do it ourselves.
            self.set_caching_headers(content, response)

            return response

    def set_caching_headers(self, content, response):
        """
        Sets caching headers based on whether or not the asset is locked.
        """

        is_locked = getattr(content, "locked", False)

        # We want to signal to the end user's browser, and to any intermediate proxies/caches,
        # whether or not this asset is cacheable.  If we have a TTL configured, we inform the
        # caller, for unlocked assets, how long they are allowed to cache it.  Since locked
        # assets should be restricted to enrolled students, we simply send headers that
        # indicate there should be no caching whatsoever.
        cache_ttl = CourseAssetCacheTtlConfig.get_cache_ttl()
        if cache_ttl > 0 and not is_locked:
            response['Expires'] = StaticContentServer.get_expiration_value(datetime.datetime.utcnow(), cache_ttl)
            response['Cache-Control'] = "public, max-age={ttl}, s-maxage={ttl}".format(ttl=cache_ttl)
        elif is_locked:
            response['Cache-Control'] = "private, no-cache, no-store"

        response['Last-Modified'] = content.last_modified_at.strftime(HTTP_DATE_FORMAT)

        remove_headers_from_response(response, "Vary")

    @staticmethod
    def get_expiration_value(now, cache_ttl):
        """Generates an RFC1123 datetime string based on a future offset."""
        expire_dt = now + datetime.timedelta(seconds=cache_ttl)
        return expire_dt.strftime(HTTP_DATE_FORMAT)

    def is_user_authorized(self, request, content, location):
        """
        Determines whether or not the user for this request is authorized to view the given asset.
        """

        is_locked = getattr(content, "locked", False)
        if not is_locked:
            return True

        if not hasattr(request, "user") or not request.user.is_authenticated():
            return False

        if not request.user.is_staff:
            deprecated = getattr(location, 'deprecated', False)
            if deprecated and not CourseEnrollment.is_enrolled_by_partial(request.user, location.course_key):
                return False
            if not deprecated and not CourseEnrollment.is_enrolled(request.user, location.course_key):
                return False

        return True

    def load_asset_from_location(self, location):
        """
        Loads an asset based on its location, either retrieving it from a cache
        or loading it directly from the contentstore.
        """

        # See if we can load this item from cache.
        content = get_cached_content(location)
        if content is None:
            # Not in cache, so just try and load it from the asset manager.
            try:
                content = AssetManager.find(location, as_stream=True)
            except (ItemNotFoundError, NotFoundError):
                raise

            # Now that we fetched it, let's go ahead and try to cache it. We cap this at 1MB
            # because it's the default for memcached and also we don't want to do too much
            # buffering in memory when we're serving an actual request.
            if content.length is not None and content.length < 1048576:
                content = content.copy_to_in_mem()
                set_cached_content(content)

        return content


def parse_range_header(header_value, content_length):
    """
    Returns the unit and a list of (start, end) tuples of ranges.

    Raises ValueError if header is syntactically invalid or does not contain a range.

    See spec for details: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.35
    """

    unit = None
    ranges = []

    if '=' in header_value:
        unit, byte_ranges_string = header_value.split('=')

        # Parse the byte ranges.
        for byte_range_string in byte_ranges_string.split(','):
            byte_range_string = byte_range_string.strip()
            # Case 0:
            if '-' not in byte_range_string:  # Invalid syntax of header value.
                raise ValueError('Invalid syntax.')
            # Case 1: -500
            elif byte_range_string.startswith('-'):
                first = max(0, (content_length + int(byte_range_string)))
                last = content_length - 1
            # Case 2: 500-
            elif byte_range_string.endswith('-'):
                first = int(byte_range_string[0:-1])
                last = content_length - 1
            # Case 3: 500-999
            else:
                first, last = byte_range_string.split('-')
                first = int(first)
                last = min(int(last), content_length - 1)

            ranges.append((first, last))

    if len(ranges) == 0:
        raise ValueError('Invalid syntax')

    return unit, ranges
