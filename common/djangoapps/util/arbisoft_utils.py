from student.models import CandidateProfile


def is_survey_required(user):
    """
    Returns True if profile survey does not exist for a user otherwise returns False
    """
    arbi_profile = CandidateProfile.objects.filter(user=user)
    return True if not arbi_profile.exists() else False