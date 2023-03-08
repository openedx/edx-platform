'''
edly Celery tasks.

'''

import logging
from urllib.parse import urlparse

from celery import task
from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import SlumberBaseException

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user

LOG = logging.getLogger(__name__)


@task()
def trigger_dataloader(partner, course_key):
    """
    Run dataloader for specific course.
    """
    catalog_integraton = CatalogIntegration.current()
    discovery_worker = catalog_integraton.get_service_user()
    user_jwt = create_jwt_for_user(discovery_worker)
    catalog_api = catalog_integraton.internal_api_url
    url_parse = urlparse(catalog_api)
    catalog_api = '{}://{}'.format(url_parse.scheme, url_parse.netloc)
    discovery_client = EdxRestApiClient(catalog_api, jwt=user_jwt)
    try:
        res = discovery_client.edly_api.v1.dataloader.post(
            {
                'partner': partner,
                'course_id': course_key,
                'service': 'lms',
            }
        )
        LOG.info(res)
    except SlumberBaseException as exp:
        LOG.exception(str(exp))
