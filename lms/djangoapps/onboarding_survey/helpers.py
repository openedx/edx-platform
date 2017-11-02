from lms.djangoapps.onboarding_survey.models import ExtendedProfile


def is_first_signup_in_org(organization):
    return ExtendedProfile.objects.filter(organization=organization).count() == 1
