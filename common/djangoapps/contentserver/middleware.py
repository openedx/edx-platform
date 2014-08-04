from django.http import (HttpResponse, HttpResponseNotModified,
    HttpResponseForbidden)
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

            response = HttpResponse(content.stream_data(), content_type=content.content_type)
            response['Last-Modified'] = last_modified_at_str

            return response
