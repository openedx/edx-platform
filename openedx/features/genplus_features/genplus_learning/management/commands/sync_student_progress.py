import logging
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand, CommandError

from openedx.features.genplus_features.genplus_learning.models import (
    Unit,
    UnitCompletion,
    UnitBlockCompletion,
)
from openedx.features.genplus_features.genplus_learning.utils import (
    get_course_completion,
    get_progress_and_completion_status
)

logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = 'Sync student progress'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument("user_ids", nargs="*", type=int)
        parser.add_argument(
            '--all-users', '--all',
            dest='all_users',
            action='store_true',
            default=False,
            help='Sync progress for user courses.',
        )

    def handle(self, *args, **options):
        print(args, options)
        if not options.get('all_users') and len(options.get('user_ids')) < 1:
            raise CommandError('At least one user or --all-users must be specified.')

        try:
            course_ids = Unit.objects.all().values_list('course', flat=True)
            filters = dict(progress__gt=0, course_key__in=course_ids)
            if not options.get('all_users'):
                filters['user_id__in'] = options.get('user_ids')
            in_progress_completion = UnitCompletion.objects.filter(**filters)
            updated_users = []
            for completion in in_progress_completion:
                user = completion.user
                course_key = completion.course_key
                course_key_str = str(course_key)
                previous_is_complete = completion.is_complete
                user_course_completion = get_course_completion(course_key_str, user, ['course'])
                if not user_course_completion:
                    continue

                progress, is_complete = get_progress_and_completion_status(
                    user_course_completion.get('total_completed_blocks'),
                    user_course_completion.get('total_blocks')
                )

                if not previous_is_complete and is_complete:
                    defaults = {
                        'progress': progress,
                        'is_complete': is_complete,
                        'completion_date': datetime.now().replace(tzinfo=pytz.UTC)
                    }
                    UnitCompletion.objects.update_or_create(user=user, course_key=course_key, defaults=defaults)
                    UnitBlockCompletion.objects.filter(course_key=course_key).update(
                        progress=progress,
                        is_complete=is_complete,
                        completion_date=datetime.now().replace(tzinfo=pytz.UTC),
                    )
                    updated_users.append(user)
                    self.stdout.write(
                        self.style.SUCCESS(f"Processed course completion of user {user}, for course {course_key}")
                    )

            self.stdout.write(f"Updated {len(updated_users)} users progress")
            self.stdout.write(self.style.SUCCESS('DONE!!'))
        except Exception as e:
            logger.exception(e)
            self.stdout.write(self.style.ERROR('FAILED!!'))
