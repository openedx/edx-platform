from course_creators.models import CourseCreator


def add_user_with_status_unrequested(user):
    """
    Adds a user to the course creator table with status 'unrequested'.
    """
    _add_user(user, 'u')


def add_user_with_status_granted(user):
    """
    Adds a user to the course creator table with status 'granted'.
    """
    _add_user(user, 'g')

def _add_user(user, state):
    if CourseCreator.objects.filter(username=user.username).count() == 0:
        entry = CourseCreator(username=user.username, state=state)
        entry.save()