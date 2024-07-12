"""
Views for serving course assets.

Historically, this was implemented as a *middleware* (StaticContentServer) that
intercepted requests with paths matching certain patterns, rather than using
urlpatterns and a view. There wasn't any good reason for this, as far as I can
tell. It causes some problems for telemetry: When the code-owner middleware asks
Django what view handled the request, it does so by looking at the result of the
`resolve` utility, but these URLs get a Resolver404 (because there's no
registered urlpattern).

We'd like to turn this into a proper view:
https://github.com/openedx/edx-platform/issues/34702

The first step, seen here, is to have urlpatterns (redundant with the
middleware's `is_asset_request` method) and a view, but the view just calls into
the same code the middleware uses. The implementation of the middleware has been
moved into StaticContentServerImpl, leaving the middleware as just a shell
around the latter.

A waffle flag chooses whether to allow the middleware to handle the request, or
whether to pass the request along to the view. Why? Because we might be relying
by accident on some weird behavior inherent to misusing a middleware this way,
and we need a way to quickly switch back if we encounter problems.

If the view works, we can move all of StaticContentServerImpl directly into the
view and drop the middleware and the waffle flag.
"""
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_safe
from edx_django_utils.monitoring import set_custom_attribute

from .middleware import CONTENT_SERVER_USE_VIEW, IMPL


@require_safe
def course_assets_view(request):
    """
    Serve course assets to end users. Colloquially referred to as "contentserver."
    """
    set_custom_attribute('content_server.handled_by.view', True)

    if not CONTENT_SERVER_USE_VIEW.is_enabled():
        # Should never happen; keep track of occurrences.
        set_custom_attribute('content_server.view.called_when_disabled', True)
        # But handle the request anyhow.

    # We'll delegate request handling to an instance of the middleware
    # until we can verify that the behavior is identical when requests
    # come all the way through to the view.
    response = IMPL.process_request(request)

    if response is None:
        # Shouldn't happen
        set_custom_attribute('content_server.view.no_response_from_impl', True)
        return HttpResponseNotFound()
    else:
        return response
