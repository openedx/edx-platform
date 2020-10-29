

from django.conf import settings
from django.core.management import call_command
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


@require_GET
def cache_programs(request):
    """
    Call the cache_programs management command.

    This view is intended for use in testing contexts where the LMS can only be
    reached over HTTP (e.g., Selenium-based browser tests). The discovery service
    API the management command attempts to call should be stubbed out first.
    """

    # checks that does site has configuration if not then
    # add a configuration with COURSE_CATALOG_API_URL parameter.
    from common.test.acceptance.fixtures import CATALOG_STUB_URL

    site_config = getattr(request.site, 'configuration', None)
    if not site_config:
        SiteConfiguration.objects.create(
            site=request.site,
            enabled=True,
            site_values={"COURSE_CATALOG_API_URL": "{catalog_url}/api/v1/".format(catalog_url=CATALOG_STUB_URL)}
        )

    if settings.FEATURES.get('EXPOSE_CACHE_PROGRAMS_ENDPOINT'):
        call_command('cache_programs')

        return HttpResponse('Programs cached.')

    raise Http404
