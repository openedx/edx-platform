import pytz
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus_learning.models import UnitCompletion, Unit
from openedx.features.genplus_features.genplus_learning.utils import get_course_completion, get_progress_and_completion_status


class Command(BaseCommand):
    help = 'Sync student progress'

    def handle(self, *args, **options):
        try:
            course_ids = Unit.objects.all().values_list('course', flat=True)
            in_progress_completion = UnitCompletion.objects.filter(progress__gt=0, course_key__in=course_ids)
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
                    updated_users.append(user)
                    self.stdout.write(self.style.SUCCESS(f"Processed course completion of user {user}, for course {course_key}"))

            self.stdout.write(f"Updated {len(updated_users)} users progress")
            self.stdout.write(self.style.SUCCESS('DONE!!'))
        except:
            self.stdout.write(self.style.ERROR('FAILED!!'))
