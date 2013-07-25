from django.http import HttpResponse, HttpResponseNotModified

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from xmodule.modulestore import InvalidLocationError
from cache_toolbox.core import get_cached_content, set_cached_content
from xmodule.exceptions import NotFoundError

import logging


class StaticContentServer(object):
    def process_request(self, request):
        # look to see if the request is prefixed with 'c4x' tag
        if request.path.startswith('/' + XASSET_LOCATION_TAG + '/'):
            logging.debug('**** path = {0}'.format(request.path))
            try:
                loc = StaticContent.get_location_from_path(request.path)
            except InvalidLocationError:
                # return a 'Bad Request' to browser as we have a malformed Location
                response = HttpResponse()
                response.status_code = 400
                return response

            # first look in our cache so we don't have to round-trip to the DB
            content = get_cached_content(loc)
            if content is None:
                # nope, not in cache, let's fetch from DB
                try:
                    logging.debug('!!!! loc = {0}'.format(loc))
                    content = contentstore().find(loc, as_stream=True)
                except NotFoundError:
                    logging.debug('**** NOT FOUND')
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

            # see if the last-modified at hasn't changed, if not return a 302 (Not Modified)

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
