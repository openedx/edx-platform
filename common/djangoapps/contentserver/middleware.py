"""
Middleware to serve assets.
"""

import logging

from django.http import (
    HttpResponse, HttpResponseNotModified, HttpResponseForbidden
)
from student.models import CourseEnrollment

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


class StaticContentServer(object):
    def process_request(self, request):
        # look to see if the request is prefixed with an asset prefix tag
        if (
            request.path.startswith('/' + XASSET_LOCATION_TAG + '/') or
            request.path.startswith('/' + AssetLocator.CANONICAL_NAMESPACE)
        ):
            if AssetLocator.CANONICAL_NAMESPACE in request.path:
                request.path = request.path.replace('block/', 'block@', 1)
            try:
                loc = StaticContent.get_location_from_path(request.path)
            except (InvalidLocationError, InvalidKeyError):
                # return a 'Bad Request' to browser as we have a malformed Location
                response = HttpResponse()
                response.status_code = 400
                return response

            # first look in our cache so we don't have to round-trip to the DB
            content = get_cached_content(loc)
            if content is None:
                # nope, not in cache, let's fetch from DB
                try:
                    content = AssetManager.find(loc, as_stream=True)
                except (ItemNotFoundError, NotFoundError):
                    response = HttpResponse()
                    response.status_code = 404
                    return response

                # since we fetched it from DB, let's cache it going forward, but only if it's < 1MB
                # this is because I haven't been able to find a means to stream data out of memcached
                if content.length is not None:
                    if content.length < 1048576:
                        # since we've queried as a stream, let's read in the stream into memory to set in cache
                        content = content.copy_to_in_mem()
                        set_cached_content(content)
            else:
                # NOP here, but we may wish to add a "cache-hit" counter in the future
                pass

            # Check that user has access to content
            if getattr(content, "locked", False):
                if not hasattr(request, "user") or not request.user.is_authenticated():
                    return HttpResponseForbidden('Unauthorized')
                if not request.user.is_staff:
                    if getattr(loc, 'deprecated', False) and not CourseEnrollment.is_enrolled_by_partial(
                        request.user, loc.course_key
                    ):
                        return HttpResponseForbidden('Unauthorized')
                    if not getattr(loc, 'deprecated', False) and not CourseEnrollment.is_enrolled(
                        request.user, loc.course_key
                    ):
                        return HttpResponseForbidden('Unauthorized')

            # convert over the DB persistent last modified timestamp to a HTTP compatible
            # timestamp, so we can simply compare the strings
            last_modified_at_str = content.last_modified_at.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

            # see if the client has cached this content, if so then compare the
            # timestamps, if they are the same then just return a 304 (Not Modified)
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
                # Data from cache (StaticContent) has no easy byte management, so we use the DB instead (StaticContentStream)
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
            response['Last-Modified'] = last_modified_at_str

            return response


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
