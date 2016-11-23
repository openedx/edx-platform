import logging

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from student.models import AnonymousUserId, anonymous_id_for_user
from submissions.models import StudentItem, ScoreAnnotation
from openassessment.assessment.models import (
    AIGradingWorkflow, Assessment, PeerWorkflow, StaffWorkflow, StudentTrainingWorkflow,
)


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Command(BaseCommand):
    help = """
    We can now have multiple anonymous user ids for a given user+course.
    This is useful if we have to change the app's SECRET_KEY, which is used to generate the anonymous user ids.
    Ref: https://github.com/edx/edx-platform/pull/13717

    However, some models don't reference the Student.AnonymousUserId model directly,
    and keep their own copies of the anonymous user ID.

    This command runs through an explicit list of those models and fields, and updates
    them to use the most recently-generated anonymous user ID.
    """

    def handle(self, *args, **options):
        """Update the anonymous IDs used by the given models and fields."""

        self.generate_anonymous_user_ids()
        anon_ids_map = self.get_old_to_new_anonymous_user_ids()

        # Update each of the old anonymous IDs with the new one.
        for (model, field_name) in (
            (StudentItem, 'student_id'),
            (ScoreAnnotation, 'creator'),
            (AIGradingWorkflow, 'student_id'),
            (Assessment, 'scorer_id'),
            (PeerWorkflow, 'student_id'),
            (StaffWorkflow, 'scorer_id'),
            (StudentTrainingWorkflow, 'student_id'),
        ):
            self.update_anonymous_user_ids(model, field_name, anon_ids_map)

    @staticmethod
    def generate_anonymous_user_ids():
        '''Generate new anonymous user id using the current settings.SECRET_KEY.'''
        for anonymous_id in AnonymousUserId.objects.all():
            anonymous_id_for_user(anonymous_id.user, anonymous_id.course_id, save=True)

    @staticmethod
    def get_old_to_new_anonymous_user_ids():
        '''Returns a mapping between each existing anonymous user id and the most recent one found in the database.'''
        user_course_id = {}
        old_to_new_anon_id = {}

        # Sort by descending id, to see the newest rows first.
        for anonymous_id in AnonymousUserId.objects.order_by('-id').all():

            # If we haven't seen this user+course combination yet, then this is the newest anonymous id.
            if not (anonymous_id.user_id, anonymous_id.course_id) in user_course_id:
                user_course_id[anonymous_id.user_id, anonymous_id.course_id] = anonymous_id.anonymous_user_id

            # If we have seen it, then newest anonymous id has already been set.
            new_anonymous_user_id = user_course_id[anonymous_id.user_id, anonymous_id.course_id]
            old_to_new_anon_id[anonymous_id.anonymous_user_id] = new_anonymous_user_id

        return old_to_new_anon_id

    @staticmethod
    def update_anonymous_user_ids(model, field_name, old_to_new_anon_id):
        '''Updates the given model.field values to use the new anonymous user id, if found.'''
        total = 0
        unchanged = 0
        updated = 0
        errors = 0
        try:
            for item in model.objects.all():
                total += 1
                old_anon_id = getattr(item, field_name)
                new_anon_id = old_to_new_anon_id.get(old_anon_id)
                if new_anon_id is not None:
                    if old_anon_id != new_anon_id:
                        try:
                            setattr(item, field_name, old_to_new_anon_id[old_anon_id])
                            item.save()
                            updated += 1
                        except (IntegrityError, ValueError) as error:
                            log.error('%s.%s cannot save: %s', model, field_name, error)
                            errors += 1
                    else:
                        unchanged += 1
                elif old_anon_id is None or old_anon_id == '':
                    # Skip record: the field value is NULL
                    unchanged += 1
                else:
                    log.error('%s.%s (id=%s) not found in anonymous user ids list?', model, field_name, item.id)
                    errors += 1

        except AttributeError as error:
            log.error('%s.%s field not found: %s', model, field_name, error)
            errors += 1

        log.info('%s.%s: updated %s of %s; %s unchanged; %s errors',
                 model, field_name, updated, total, unchanged, errors)

