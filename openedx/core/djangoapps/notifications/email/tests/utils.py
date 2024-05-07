"""
Utils for tests
"""
from openedx.core.djangoapps.notifications.models import Notification


def create_notification(user, course_key, **kwargs):
    """
    Create a test notification
    """
    notification_params = {
        'user': user,
        'course_id': course_key,
        'app_name': "discussion",
        'notification_type': "new_comment",
        'content_url': '',
        'content_context': {
            "replier_name": "replier",
            "username": "username",
            "author_name": "author_name",
            "post_title": "post_title",
            "course_update_content": "Course update content",
            "content_type": 'post',
            "content": "post_title"
        },
        'email': True,
        'web': True
    }
    notification_params.update(kwargs)
    notification = Notification.objects.create(**notification_params)
    return notification


def assert_list_equal(list_1, list_2):
    """
    Asserts if list is equal
    """
    assert len(list_1) == len(list_2)
    for element in list_1:
        assert element in list_2
