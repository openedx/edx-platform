import logging

from django.http import HttpResponse, Http404

from xmodule.contentstore.django import contentstore
from xmodule.contentstore import StaticContent
from cache_toolbox.core import get_cached_content, set_cached_content
from xmodule.exceptions import NotFoundError


class StaticContentServer(object):
    def __init__(self):
        self.match_tag = StaticContent.get_location_tag()

    def process_request(self, request):
        # look to see if the request is prefixed with 'c4x' tag
        if request.path.startswith('/' + self.match_tag):

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
                logging.debug('cache hit on {0}'.format(content.filename))

            response = HttpResponse(content.data, content_type=content.content_type)
            response['Content-Disposition'] = 'attachment; filename={0}'.format(content.name)
            
            return response
