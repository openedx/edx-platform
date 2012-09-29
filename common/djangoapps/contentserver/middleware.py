import logging
import time

from django.http import HttpResponse, Http404, HttpResponseNotModified

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from cache_toolbox.core import get_cached_content, set_cached_content
from xmodule.exceptions import NotFoundError


class StaticContentServer(object):
    def process_request(self, request):
        # look to see if the request is prefixed with 'c4x' tag
        if request.path.startswith('/' + XASSET_LOCATION_TAG):

            # first look in our cache so we don't have to round-trip to the DB
            content = get_cached_content(request.path)
            if content is None:
                # nope, not in cache, let's fetch from DB
                try:
                    content = contentstore().find(request.path)
                except NotFoundError:
                    raise Http404

                # since we fetched it from DB, let's cache it going forward
                set_cached_content(content)
            else:
                # @todo: we probably want to have 'cache hit' counters so we can
                # measure the efficacy of our caches
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

            response = HttpResponse(content.data, content_type=content.content_type)
            response['Last-Modified'] = last_modified_at_str

            return response
