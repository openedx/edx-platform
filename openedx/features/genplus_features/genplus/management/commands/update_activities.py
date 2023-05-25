from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.models import JournalPost, Activity
from openedx.features.genplus_features.genplus.constants import ActivityTypes, JournalTypes


class Command(BaseCommand):
    help = 'Update Activities'

    def handle(self, *args, **options):
        # delete all JournalPost related Activities
        Activity.objects.filter(type__in=(ActivityTypes.JOURNAL_ENTRY_BY_STUDENT,
                                          ActivityTypes.JOURNAL_ENTRY_BY_TEACHER))
        for journal in JournalPost.objects.all():
            actor_obj = None
            if journal.journal_type == JournalTypes.STUDENT_POST:
                actor_obj = journal.student
                activity_type = ActivityTypes.JOURNAL_ENTRY_BY_STUDENT
            elif journal.journal_type == JournalTypes.TEACHER_FEEDBACK:
                actor_obj = journal.teacher
                activity_type = ActivityTypes.JOURNAL_ENTRY_BY_TEACHER
            # creating/updating individual object to prevent auto created/modified datetime
            activity = Activity(
                actor=actor_obj,
                type=activity_type,
                action_object=journal,
                target=journal.student
            )
            activity.save()
            activity.refresh_from_db()
            Activity.objects.filter(pk=activity.pk).update(modified=journal.modified, created=journal.created)

