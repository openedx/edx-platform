from logging import getLogger

from django.core.management.base import BaseCommand

from lms.djangoapps.onboarding.choices import FUNCTIONS, GOALS, HEAR_ABOUT_PHILANTHROPY, INTERESTED_LEARNERS, INTERESTS
from lms.djangoapps.onboarding.models import UserExtendedProfile

log = getLogger(__name__)

ERROR_MSG_MISMATCH = '{field_name} did not match for Profile ID: {profile_id}, User ID: {user_id}. ' \
                     'Expected Value: {expected_val}, Actual Value: {actual_val}'


def compare_function_areas(user_extended_profile):
    expected_value = set([k for k, _ in FUNCTIONS if getattr(user_extended_profile, k)])
    actual_value = set(user_extended_profile.function_areas)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='FUNCTION_AREAS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))


def compare_interests(user_extended_profile):
    expected_value = set([k for k, _ in INTERESTS if getattr(user_extended_profile, k)])
    actual_value = set(user_extended_profile.interests)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='INTERESTS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))


def compare_learners_related(user_extended_profile):
    expected_value = set([k for k, _ in INTERESTED_LEARNERS if getattr(user_extended_profile, k)])
    actual_value = set(user_extended_profile.learners_related)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='LEARNERS_RELATED',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))


def compare_goals(user_extended_profile):
    expected_value = set([k for k, _ in GOALS if getattr(user_extended_profile, k)])
    actual_value = set(user_extended_profile.goals)

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='GOALS',
                                            profile_id=user_extended_profile.id,
                                            user_id=user_extended_profile.user_id,
                                            expected_val=expected_value,
                                            actual_val=actual_value))


def compare_hear_about_philanthropyu(user_extended_profile):
    expected_value = get_expected_hear_about_philanthropyu(user_extended_profile)

    hear_about_philanthropyu_list = list(user_extended_profile.hear_about_philanthropyu)
    actual_value = hear_about_philanthropyu_list[0] if len(hear_about_philanthropyu_list) > 0 else ''

    if expected_value != actual_value:
        log.error(ERROR_MSG_MISMATCH.format(field_name='HEAR_ABOUT_PHILANTHROPYU',
                                           profile_id=user_extended_profile.id,
                                           user_id=user_extended_profile.user_id,
                                           expected_val=expected_value,
                                           actual_val=actual_value))


def get_expected_hear_about_philanthropyu(user_extended_profile):
    hear_about_philanthropy = user_extended_profile.hear_about_philanthropy
    hear_about_philanthropy_other = user_extended_profile.hear_about_philanthropy_other

    if hear_about_philanthropy is None:
        return ''

    if hear_about_philanthropy == 'Other':
        if hear_about_philanthropy_other is not None and hear_about_philanthropy_other != '':
            return hear_about_philanthropy_other

        return ''

    for i in range(len(HEAR_ABOUT_PHILANTHROPY)):
        if hear_about_philanthropy == HEAR_ABOUT_PHILANTHROPY[i][1]:
            return HEAR_ABOUT_PHILANTHROPY[i][0]


class Command(BaseCommand):
    help = """
        This is a one-time command that will be executed after the data migration query for onboarding model
        optimization. The purpose of this command is to ensure data consistency between the old fields and the
        newly added fields in the UserExtendedProfile model, thereby ensuring that no data is lost in the migration
        """

    def handle(self, *args, **options):
        user_extended_profiles = UserExtendedProfile.objects.all()
        for user_extended_profile in user_extended_profiles:
            compare_function_areas(user_extended_profile)
            compare_interests(user_extended_profile)
            compare_learners_related(user_extended_profile)
            compare_goals(user_extended_profile)
            compare_hear_about_philanthropyu(user_extended_profile)
