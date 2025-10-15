# Creating a new notification

This documentation provides instructions to developers on how to add new notifications to the existing notification system.

## Overview of terms

* Type: every notification a user sees has a defined type. This type describes the notification's behaviour and template text.
* App: each notification type is associated with a notification app. A notification app is simply a way to group notifications, and to provide a mechanism for shared behaviour.
* Core notification: a notification type can be labelled as a core notification. In this case, the behaviour is managed at the app level, not at the level of the individual notification type.

## Defining a notification

The configuration consists of notification types and notification apps. Follow the steps below to define a new notification type.

### Step 1: Define the Notification App

The first step to defining a new notification is deciding on an app to associate it with. Either choose an existing one or create a new one in `COURSE_NOTIFICATION_APPS` in [base_notification.py](../base_notification.py). For example, here is an app named "discussion":

```python
COURSE_NOTIFICATION_APPS = {
    'discussion': {
        'enabled': True,
        'core_info': '',
        'core_web': True,
        'core_email': True,
        'core_push': True,
        'non_editable': [],
        'core_email_cadence': 'weekly'
    }
}
```

The app name (the key) can be any name you wish to add but ideally it should represent existing Django apps in the project.
For an explanation of the available fields, see `NotificationApp` in [base_notification.py](../base_notification.py).

### **Step 2: Define the Notification Type**

Now you can define the notification type itself.
To do this, add a new entry to `COURSE_NOTIFICATION_TYPES` in [base_notification.py](../base_notification.py).
For example, here is a notification defined for a new response to a discussion forum post, associated with the "discussion" app example from the previous step:

```python
COURSE_NOTIFICATION_TYPES = {
    'new_response': {
        'notification_app': 'discussion',
        'name': 'new_response',
        'is_core': False,
        'web': True,
        'email': True,
        'push': True,
        'info': 'Response on post',
        'non_editable': [],
        'content_template': _('<{p}><{strong}>{replier_name}</{strong}> responded to your post <{strong}>{post_title}</{strong}></{p}>'),
        'content_context': {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        },
        'email_template': '',
    },
}
```

For an explanation of the available fields, see `NotificationType` in [base_notification.py](../base_notification.py).

### Step 3: Update the version in the model file

Newly added types are only usable once you have updated the value of `COURSE_NOTIFICATION_CONFIG_VERSION` in [notifications/models.py](../models.py).
This constant is used to track changes in notification configuration, and whenever this version is updated preferences of users are also updated with newly available types.
To update it, increment the value by 1.

Adding new notification types without this step will have no effect.
You don't need to update the constant for changes that are not stored in database (eg. templates).

Now the notification type is defined and ready to use!
The next section details how to use this notification type to create and send a notification.

## Sending a notification

To send a notification, you need to send the `USER_NOTIFICATION_REQUESTED` signal with an instance of `UserNotificationData` containing information about the notification to send.

Below is an example function to build and send the `new_response` notification type from earlier.

from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED
from openedx_events.learning.data import UserNotificationData

```python
def send_new_response_notification(user_ids, course, thread, replier_user):
    notification_data = UserNotificationData(
        user_ids=user_ids,
        notification_type="new_response",
        content_url=f"/{course.id}/posts/{thread.id}",
        app_name='discussion',
        course_key=course.id,
        context={
            'post_title': thread.title,
            'replier_name': replier_user.username,
        },
    )
    USER_NOTIFICATION_REQUESTED.send_event(notification_data=notification_data)
```

Explanation of the parameters for `UserNotificationData`:

| Name | Type | Description |
| :---- | :---- | :---- |
| `user_ids` | `list[int]` | List of user IDs to send the notification to. |
| `notification_type` | `str` | The type of notification to send. This must be a key of `COURSE_NOTIFICATION_TYPES`. |
| `content_url` | `str` | Url the user will navigate to if they click on the notification. |
| `app_name` | `str` | The app this notification is associated with. This must be a key of `COURSE_NOTIFICATION_APPS`. |
| `course_key` | `CourseKey` | The course that this notification will be associated with. |
| `context` | `dict[str, str]` | Context variables and values to pass to the notification content template. Keys are the variable names defined in the notification type. |

That's it! You have implemented the code to send a new user notification using the `USER_NOTIFICATION_REQUESTED` signal.

## Grouping notifications

For some notification types, the volume for a learner can be huge and can cause annoyance.
For example, if a learner creates a post, and other learners and staff members start adding responses to his post, if for each comment, we add a response, it could result in dozens of notifications.
To avoid these scenarios, we have implemented a feature that allows grouping more than one similar notifications into a single notification.
Steps to group a notification:

1. Enable grouping waffle flag `notifications.enable_notification_grouping`.
2. Add `group_by_id` in context before sending the `USER_NOTIFICATION_REQUESTED` event (see [discussions_notifications.py](../../../../../lms/djangoapps/discussion/rest_api/discussions_notifications.py), and search for `group_by_id` for an example).
3. Implement a grouper class to modify content_context (see [grouping_notifications.py](../grouping_notifications.py) for an example).

## Legal

When adding a new notification type, you will need a Privacy threshold assessment done by legal.

## Troubleshooting

If you have followed the above steps and notifications are still not working, check if the `notifications.enable_notifications` waffle flag is enabled.
