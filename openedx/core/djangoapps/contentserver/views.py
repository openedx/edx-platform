"""
Views for serving course assets.

Historically, this was implemented as a *middleware* (StaticContentServer) that
intercepted requests with paths matching certain patterns, rather than using
urlpatterns and a view. There wasn't any good reason for this, as far as I can
tell. It causes some problems for telemetry: When the code-owner middleware asks
Django what view handled the request, it does so by looking at the result of the
`resolve` utility, but these URLs get a Resolver404 (because there's no
registered urlpattern).

We've turned it into a proper view, with a few warts remaining:

- The view implementation is all bundled into a StaticContentServer class that
  doesn't appear to have any state. The methods could likely just be extracted
  as top-level functions.
- All three urlpatterns are registered to the same view, which then has to
  re-parse the URL to determine which pattern is in effect. We should probably
  have 3 views as entry points.
"""
from django.views.decorators.http import require_safe

from .middleware import IMPL


@require_safe
def course_assets_view(request):
    """
    Serve course assets to end users. Colloquially referred to as "contentserver."
    """
    return IMPL.process_request(request)
