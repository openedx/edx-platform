import logging
import sys

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import BaseCommand

from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL, PROGRAM_UUIDS_CACHE_KEY
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.utils import create_catalog_api_client


logger = logging.getLogger(__name__)
User = get_user_model()  # pylint: disable=invalid-name


class Command(BaseCommand):
    """Management command used to cache program data.

    This command requests every available program from the discovery
    service, writing each to its own cache entry with an indefinite expiration.
    It is meant to be run on a scheduled basis and should be the only code
    updating these cache entries.
    """
    help = "Rebuild the LMS' cache of program data."

    def handle(self, *args, **options):
        catalog_integration = CatalogIntegration.current()
        username = catalog_integration.service_username

        try:
            user = User.objects.get(username=username)
            client = create_catalog_api_client(user, catalog_integration)
        except User.DoesNotExist:
            logger.error(
                'Failed to create API client. Service user {username} does not exist.'.format(username)
            )
            raise

        try:
            querystring = {
                'exclude_utm': 1,
                'status': ('active', 'retired'),
                'uuids_only': 1,
            }

            logger.info('Requesting program UUIDs.')
            uuids = client.programs.get(**querystring)
        except:  # pylint: disable=bare-except
            logger.error('Failed to retrieve program UUIDs.')
            raise

        total = len(uuids)
        logger.info('Received {total} UUIDs.'.format(total=total))

        programs = {}
        failure = False
        for uuid in uuids:
            try:
                logger.info('Requesting details for program {uuid}.'.format(uuid=uuid))
                program = client.programs(uuid).get(exclude_utm=1)

                cache_key = PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)
                programs[cache_key] = program
            except:  # pylint: disable=bare-except
                logger.exception('Failed to retrieve details for program {uuid}.'.format(uuid=uuid))
                failure = True

                continue

        successful = len(programs)
        logger.info('Caching details for {successful} programs.'.format(successful=successful))
        cache.set_many(programs, None)

        logger.info('Caching UUIDs for {total} programs.'.format(total=total))
        cache.set(PROGRAM_UUIDS_CACHE_KEY, uuids, None)

        if failure:
            # This will fail a Jenkins job running this command, letting site
            # operators know that there was a problem.
            sys.exit(1)
