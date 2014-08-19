from django.http import (
    HttpResponse, HttpResponseNotModified, HttpResponseForbidden
)
from student.models import CourseEnrollment

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from xmodule.modulestore import InvalidLocationError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import AssetLocator
from cache_toolbox.core import get_cached_content, set_cached_content
from xmodule.exceptions import NotFoundError

# TODO: Soon as we have a reasonable way to serialize/deserialize AssetKeys, we need
# to change this file so instead of using course_id_partial, we're just using asset keys


class StaticContentServer(object):
    def process_request(self, request):
        # look to see if the request is prefixed with an asset prefix tag
        if (
            request.path.startswith('/' + XASSET_LOCATION_TAG + '/') or
            request.path.startswith('/' + AssetLocator.CANONICAL_NAMESPACE)
        ):
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
                    content = contentstore().find(loc, as_stream=True)
                except NotFoundError:
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
            response = None
            if request.META.get('HTTP_RANGE'):
                # Data from cache (StaticContent) has no easy byte management, so we use the DB instead (StaticContentStream)
                if type(content) == StaticContent:
                    content = contentstore().find(loc, as_stream=True)

                # Let's parse the Range header, bytes=first-[last]
                range_header = request.META['HTTP_RANGE']
                if '=' in range_header:
                    unit, byte_range = range_header.split('=')
                    # "Accept-Ranges: bytes" tells the user that only "bytes" ranges are allowed
                    if unit == 'bytes' and '-' in byte_range:
                        first, last = byte_range.split('-')
                        # "first" must be a valid integer
                        try:
                            first = int(first)
                        except ValueError:
                            pass
                        if type(first) is int:
                            # "last" default value is the last byte of the file
                            # Users can ask "bytes=0-" to request the whole file when they don't know the length
                            try:
                                last = int(last)
                            except ValueError:
                                last = content.length - 1

                            if 0 <= first <= last < content.length:
                                # Valid Range attribute
                                response = HttpResponse(content.stream_data_in_range(first, last))
                                response['Content-Range'] = 'bytes {first}-{last}/{length}'.format(
                                    first=first, last=last, length=content.length
                                )
                                response['Content-Length'] = str(last - first + 1)
                                response.status_code = 206  # HTTP_206_PARTIAL_CONTENT
                if not response:
                    # Malformed Range attribute
                    response = HttpResponse()
                    response.status_code = 400  # HTTP_400_BAD_REQUEST
                    return response

            else:
                # No Range attribute
                response = HttpResponse(content.stream_data())
                response['Content-Length'] = content.length

            response['Accept-Ranges'] = 'bytes'
            response['Content-Type'] = content.content_type
            response['Last-Modified'] = last_modified_at_str

            return response
