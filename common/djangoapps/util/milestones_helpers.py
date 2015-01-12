"""
Utility library for working with the edx-milestones app
"""
NAMESPACE_CHOICES = {
    'ENTRANCE_EXAM': 'entrance_exams'
}


def generate_milestone_namespace(namespace, course_key=None):
    """
    Returns a specifically-formatted namespace string for the specified type
    """
    if namespace in NAMESPACE_CHOICES.values():
        if namespace == 'entrance_exams':
            return '{}.{}'.format(unicode(course_key), NAMESPACE_CHOICES['ENTRANCE_EXAM'])


def serialize_user(user):
    """
    Returns a milestones-friendly representation of a user object
    """
    return {
        'id': user.id,
    }
