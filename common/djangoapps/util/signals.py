"""
https://docs.djangoproject.com/en/dev/topics/signals/
"""
from django.dispatch import Signal

# Platform Event: Course Deleted
# * Broadcasts to listeners when a particular course has been removed from the system
# * Important because Courses are not Django ORM entities, so model events aren't available
course_deleted = Signal(providing_args=["course"])  # pylint: disable=C0103
