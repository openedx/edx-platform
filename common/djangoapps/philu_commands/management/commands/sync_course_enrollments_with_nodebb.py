from logging import getLogger

from django.core.management.base import BaseCommand

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

from nodebb.helpers import get_community_id
from nodebb.tasks import task_join_group_on_nodebb
from student.models import CourseEnrollment

log = getLogger(__name__)


class Command(BaseCommand):
    help = 'Get all enrolled user(s) of given course(s) and add them to respective nodebb group.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course_ids',
            action='append',
            help='Sync enrollments of this/these course id(s)',
        )

    def _get_course_active_enrollments(self, course_id):
        return CourseEnrollment.objects.filter(course_id=course_id, is_active=True)

    def handle(self, *args, **options):
        course_ids = options['course_ids']

        for course_id in course_ids:
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                log.error('Invalid course id provided: {}'.format(course_id))
                continue

            community_id = get_community_id(course_key)
            if not community_id:
                # Either course id doesn't exist in database or community against this course is not made
                log.error('Either course or community not found for course id {}'.format(course_id))
                continue

            enrollments = self._get_course_active_enrollments(course_key)

            for enrollment in enrollments:
                username = enrollment.user.username
                task_join_group_on_nodebb.delay(category_id=community_id, username=username)
                log.info(
                    'Task to sync enrollment of {course} '
                    'for {username} in community:{community} is added to celery'.format(
                        course=course_id,
                        username=username,
                        community=community_id
                    )
                )
