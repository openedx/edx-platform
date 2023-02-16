"""
APIs providing enterprise context for events.
"""
try:
    from enterprise.models import EnterpriseCourseEnrollment
except ImportError:  # pragma: no cover
    pass


def get_enterprise_event_context(user_id, course_id):
    """
    Creates an enterprise context from a `course_id` anf `user_id`.
    Example Returned Context::
        {
            'enterprise_uuid': '1a0fbcbe-49e5-42f1-8e83-4cddfa592f22'
        }
    Arguments:
        user_id: id of user object.
        course_id: id of course object.
    Returns:
        dict: A dictionary representing the enterprise uuid.
    """
    # Prevent a circular import.
    from openedx.features.enterprise_support.utils import is_enterprise_learner
    context = {}
    if is_enterprise_learner(user_id):
        uuids = EnterpriseCourseEnrollment.get_enterprise_uuids_with_user_and_course(str(user_id), str(course_id))
        if uuids:
            context.update({"enterprise_uuid": str(uuids[0])})
    return context
