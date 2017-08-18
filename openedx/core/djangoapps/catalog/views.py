import logging
from django.conf import settings
from django.core.management import call_command
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
logger = logging.getLogger(__name__)


@require_GET
def cache_programs(request):

    logger.error("cache ----------------")
    from common.test.acceptance.fixtures import CATALOG_STUB_URL
    COURSE_CATALOG_API_URL = "{catalog_url}/api/v1/".format(catalog_url=CATALOG_STUB_URL)
    site = request.site
    logger.error(site)
    SiteConfiguration.objects.create(
        site=request.site,
        enabled=True,
        values={"COURSE_CATALOG_API_URL": COURSE_CATALOG_API_URL}
    )
    if settings.FEATURES.get('EXPOSE_CACHE_PROGRAMS_ENDPOINT'):
        call_command('cache_programs')

        return HttpResponse('Programs cached.')

    raise Http404


@require_GET
def cache_programs_test(request):
    """
    Call the cache_programs management command.

    This view is intended for use in testing contexts where the LMS can only be
    reached over HTTP (e.g., Selenium-based browser tests). The discovery service
    API the management command attempts to call should be stubbed out first.
    """

    try:
        from common.test.acceptance.fixtures import CATALOG_STUB_URL
        COURSE_CATALOG_API_URL = "{catalog_url}/api/v1/".format(catalog_url=CATALOG_STUB_URL)
        site = request.site
        logger.error(site)
    except Exception as e:
        logger.error("view exception -asdf")
        logger.error(e)
    SiteConfiguration.objects.create(
        site=request.site,
        enabled=True,
        values={"COURSE_CATALOG_API_URL": COURSE_CATALOG_API_URL}
    )
    if settings.FEATURES.get('EXPOSE_CACHE_PROGRAMS_ENDPOINT'):
        call_command('cache_programs')

        return HttpResponse('Programs cached.')

    raise Http404
