""""Management command to add course run information to the cache."""

import logging
import sys
from urllib.parse import quote_plus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import BaseCommand

from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.catalog.cache import COURSE_RUN_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.utils import get_catalog_api_base_url, get_catalog_api_client
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

EXEC_ED_COURSE_TYPE = "executive-education-2u"
BEST_MODE_ORDER = [
    CourseMode.VERIFIED,
    CourseMode.PROFESSIONAL,
    CourseMode.NO_ID_PROFESSIONAL_MODE,
    CourseMode.UNPAID_EXECUTIVE_EDUCATION,
    CourseMode.AUDIT,
]

logger = logging.getLogger(__name__)
User = get_user_model()  # pylint: disable=invalid-name


class Command(BaseCommand):
    """Management command used to cache course run data.

    This command requests data for every available courserun from the discovery
    service, writing each to its own cache entry with an indefinite expiration.
    It is meant to be run on a scheduled basis and should be the only code
    updating these cache entries.
    """
    help = "Rebuild the LMS' cache of course runs data."

    # lint-amnesty, pylint: disable=bad-option-value, unicode-format-string
    def handle(self, *args, **options):  # lint-amnesty, pylint: disable=too-many-statements
        catalog_integration = CatalogIntegration.current()
        username = catalog_integration.service_username

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.exception(
                f'Failed to create API client. Service user {username} does not exist.'
            )
            raise

        client = get_catalog_api_client(user)
        api_base_url = get_catalog_api_base_url()

        # TODO: Which courses we should consider and which courses we should exclude?
        # TODO: What to do with old style course keys?
        all_courserun_keys = CourseOverview.get_all_courses().values_list('id', flat=True)
        for courserun_keys in self.chunks(all_courserun_keys):

            course_details = self.fetch_courses_details(client, courserun_keys, api_base_url)
            processed_courses_details = self.process_courses_details(courserun_keys, course_details)

            courserun_keys_list = map(str, courserun_keys)
            logger.info(f'Caching details for {courserun_keys_list} courses.')
            cache.set_many(processed_courses_details, None)

        logger.info(f'Caching completed for all courses.')

    @classmethod
    def fetch_courses_details(cls, client, courserun_keys, api_base_url):  # lint-amnesty, pylint: disable=missing-function-docstring
        """
        Fetch the course data from discovery using `/api/v1/courses` endpoint
        """
        course_keys = [cls.construct_course_key(courserun_key) for courserun_key in courserun_keys]
        encoded_course_keys = ','.join(map(quote_plus, course_keys))

        logger.info(f'Fetching details for courses {course_keys}.')
        api_url = f"{api_base_url}/courses/?keys={encoded_course_keys}"
        response = client.get(api_url)
        response.raise_for_status()
        courses_details = response.json()
        results = courses_details.get('results', [])

        return results

    @classmethod
    def process_courses_details(cls, courserun_keys, courses_details):
        """
        Parse and extract the minimal data that we need.
        """
        courses = {}
        for courserun_key in courserun_keys:
            course_key = cls.construct_course_key(courserun_key)
            courserun_key = str(courserun_key)
            course_metadata = cls.find_attr(courses_details, 'key', course_key)

            course_type = course_metadata.get('course_type')
            product_source = course_metadata.get('product_source')
            if product_source:
                product_source = product_source.get('slug')

            enroll_by = start_date = end_date = None

            if course_type == EXEC_ED_COURSE_TYPE:
                additional_metadata = course_metadata.get('additional_metadata')
                if additional_metadata:
                    enroll_by = additional_metadata.get('registration_deadline')
                    start_date = additional_metadata.get('start_date')
                    end_date = additional_metadata.get('end_date')
            else:
                course_run = cls.find_attr(course_metadata.get('course_runs'), 'key', courserun_key)
                seat = cls.find_best_mode_seat(course_run.get('seats'))
                enroll_by = seat.get('upgrade_deadline')
                start_date = course_run.get('start')
                end_date = course_run.get('end')

            course_data = {
                'course_type': course_type,
                'product_source': product_source,
                'enroll_by': enroll_by,
                'start_date': start_date,
                'end_date': end_date,
            }
            courses[COURSE_RUN_CACHE_KEY_TPL.format(courserun_key=courserun_key)] = course_data

        return courses

    @classmethod
    def find_best_mode_seat(cls, seats):
        """
        Find the seat by best course mode
        """
        return sorted(seats, key=lambda x: BEST_MODE_ORDER.index(x['type']))[0]

    @classmethod
    def chunks(cls, keys, chunk_size=50):
        """
        Yield chunks of size `chunk_size`
        """
        for i in range(0, len(keys), chunk_size):
            yield keys[i:i + chunk_size]

    @staticmethod
    def construct_course_key(course_locator):
        """
        Construct course key from course run key.
        """
        # TODO: What to do with old sytle course and course run keys?
        return f'{course_locator.org}+{course_locator.course}'

    @classmethod
    def find_attr(cls, iterable, attr_name, attr_value):
        """
        Find value of an attribute from with in an iterable.
        """
        for item in iterable:
            if item[attr_name] == attr_value:
                return item
