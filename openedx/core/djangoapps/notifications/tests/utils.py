"""
Utils for tests
"""
from openedx.core.djangoapps.notifications.models import Notification


def create_notification(user, course_key, **kwargs):
    """
    Create a  notification
    """
    params = {
        'user': user,
        'course_id': course_key,
        'app_name': 'discussion',
        'notification_type': 'new_comment',
        'content_url': '',
        'content_context': {
            "replier_name": "replier",
            "username": "username",
            "author_name": "author_name",
            "post_title": "post_title",
            "course_update_content": "Course update content",
            "content_type": 'post',
            "content": "post_title"
        }
    }
    params.update(kwargs)
    notification = Notification.objects.create(**params)
    return notification
