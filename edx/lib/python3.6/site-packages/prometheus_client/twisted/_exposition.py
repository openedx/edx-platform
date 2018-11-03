from __future__ import absolute_import, unicode_literals

from twisted.web.resource import Resource

from .. import REGISTRY, exposition


class MetricsResource(Resource):
    """
    Twisted ``Resource`` that serves prometheus metrics.
    """
    isLeaf = True

    def __init__(self, registry=REGISTRY):
        self.registry = registry

    def render_GET(self, request):
        encoder, content_type = exposition.choose_encoder(request.getHeader('Accept'))
        request.setHeader(b'Content-Type', content_type.encode('ascii'))
        return encoder(self.registry)
