"""utils for feature-based enrollments"""


from common.djangoapps.student.models import FBEEnrollmentExclusion


def is_in_holdback(enrollment):
    """
    Return true if given user is in holdback expermiment
    """
    in_holdback = False
    if enrollment is not None:
        try:
            if enrollment.fbeenrollmentexclusion:
                return True
        except FBEEnrollmentExclusion.DoesNotExist:
            pass

    return in_holdback
