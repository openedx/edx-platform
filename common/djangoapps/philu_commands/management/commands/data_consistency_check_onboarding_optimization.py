from logging import getLogger

from django.core.management.base import BaseCommand

from lms.djangoapps.onboarding.choices import (
    FUNCTIONS,
    GOALS,
    HEAR_ABOUT_PHILANTHROPY_DICT,
    INTERESTED_LEARNERS,
    INTERESTS
)
from lms.djangoapps.onboarding.models import UserExtendedProfile

log = getLogger(__name__)

ERROR_MSG_MISMATCH = """
    {field_name} did not match for Profile ID: {profile_id}, User ID: {user_id}.
    Expected Value: {expected_val}
    Actual Value: {actual_val}
"""


def get_selected_choices_keys(user_extended_profile, choices):
    return list([k for k, _ in choices if getattr(user_extended_profile, k)])


def compare_function_areas(user_extended_profile):
    expected_value = get_selected_choices_keys(user_extended_profile, FUNCTIONS)
    actual_value = list(user_extended_profile.function_areas)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='FUNCTION_AREAS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))

        return False

    return True


def compare_interests(user_extended_profile):
    expected_value = get_selected_choices_keys(user_extended_profile, INTERESTS)
    actual_value = list(user_extended_profile.interests)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='INTERESTS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))

        return False

    return True


def compare_learners_related(user_extended_profile):
    expected_value = get_selected_choices_keys(user_extended_profile, INTERESTED_LEARNERS)
    actual_value = list(user_extended_profile.learners_related)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='LEARNERS_RELATED',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))

        return False

    return True


def compare_goals(user_extended_profile):
    expected_value = get_selected_choices_keys(user_extended_profile, GOALS)
    actual_value = list(user_extended_profile.goals)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='GOALS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))

        return False

    return True


def compare_hear_about_philanthropyu(user_extended_profile):
    expected_value = get_expected_hear_about_philanthropyu(user_extended_profile)

    hear_about_philanthropyu_list = list(user_extended_profile.hear_about_philanthropyu)
    actual_value = hear_about_philanthropyu_list[0] if hear_about_philanthropyu_list else ''

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='HEAR_ABOUT_PHILANTHROPYU',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))

        return False

    return True


def get_expected_hear_about_philanthropyu(user_extended_profile):
    hear_about_philanthropy = user_extended_profile.hear_about_philanthropy
    hear_about_philanthropy_other = user_extended_profile.hear_about_philanthropy_other

    if hear_about_philanthropy is None:
        return ''

    if hear_about_philanthropy == 'Other':
        return hear_about_philanthropy_other

    for key, value in HEAR_ABOUT_PHILANTHROPY_DICT.items():
        if hear_about_philanthropy == value:
            return key


class Command(BaseCommand):
    help = """
        This is a one-time command that will be executed after the data migration query for onboarding model
        optimization. The purpose of this command is to ensure data consistency between the old fields and the
        newly added fields in the UserExtendedProfile model, thereby ensuring that no data is lost in the migration
    """

    def handle(self, *args, **options):
        user_extended_profiles = UserExtendedProfile.objects.all()

        all_profiles_count = len(user_extended_profiles)
        processed_profiles_count = 0
        failed_profiles = []

        for user_extended_profile in user_extended_profiles:
            comparison_statuses = [
                compare_function_areas(user_extended_profile),
                compare_interests(user_extended_profile),
                compare_learners_related(user_extended_profile),
                compare_goals(user_extended_profile),
                compare_hear_about_philanthropyu(user_extended_profile)
            ]

            if not all(comparison_statuses):
                failed_profiles.append(int(user_extended_profile.id))

            processed_profiles_count += 1
            log.info('{processed}/{all} profiles processed'.
                     format(processed=processed_profiles_count, all=all_profiles_count))

        if failed_profiles:
            log.info('{failed}/{all} profiles failed'.format(failed=len(failed_profiles), all=all_profiles_count))
            log.info('IDs of failed profiles:')
            log.info(failed_profiles)
        else:
            log.info('Congratulations! Consistency check is complete and there are no failed profiles.')
