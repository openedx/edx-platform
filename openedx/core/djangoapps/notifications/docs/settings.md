### How to override default notification preferences

This document explains how to override notification preferences defaults for new users who sign up on the platform. Learn more about notification, preferences and defaults here: https://docs.openedx.org/en/latest/learners/sfd_notifications/index.html

**Note:** These overrides will only apply to new users who sign up after the override has been configured.

### Definitions

**Notification:** An alert that goes out to the user as a result of some activity e.g. "Mark responded to your post" etc.

**Notification Preference:** A per-user setting for each notification type (web, email etc.). This is explained in the table below.

**Notification apps:** For organization purposes, notification preferences are grouped by apps/platform workflows that they are related to. As of now, we have 3 apps: discussions, grading, and updates. Note that there is no app-level on/off switch for notifications types in it.

**Bundled preferences:** Each app discussed above has a set of preferences that start with `core_*` (e.g., `core_web`, `core_email`, `core_email_cadence`). A notification type marked `is_core: True` inherits its preferences from the app's `core_*` preferences instead of using its own default preferences. This enables us to bundle several notification types under one row of preferences visible to the user. For example, in case of discussions, 7 notifications types are controlled by `core_*` preference of the discussions app, which appears on the Account Settings page as a single row labeled "Activity Notifications" (see details here: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/4750475268/Current+state+of+OpenedX+Notifications#Activities%2C-Preferences-and-Defaults). This reduces clutter on the settings page.

### What you can override

The table below lists all the preferences that you can override for each notification along with possible values. You can override defaults for both using the following dictionaries in your `lms.yml`, `cms.yml`, or `settings.py`:

- Use `NOTIFICATION_TYPES_OVERRIDE` to override defaults for notifications.
- Use `NOTIFICATION_APPS_OVERRIDE` to override defaults for notifications marked as core (`is_core: True`). Instead of notification key, use the app key here. At present, there are 3 apps whose keys are as follows:
  - discussion
  - updates
  - grading

| Key | Key for notifications marked as core | Type | Possible values | What it does |
|-----|--------------------------------------|------|-----------------|--------------|
| web | core_web | bool | True OR False | Determines if the user gets notifications in the tray. |
| email | core_email | bool | True OR False | Determines if the user gets notification in email. |
| push | core_push | bool | True OR False | Determines if user gets push notification in mobile apps (not implemented) |
| email_cadence | core_email_cadence | string | 'Immediately' OR 'Daily' OR 'Weekly' | Determines when a user receives email notification. |
| non_editable | non_editable | list of strings | Any subset of ['web','email','push'] e.g. ['email', 'web'] | Determines toggles of which of the 3 channels will not be editable by the user. |

Notification keys are listed in the table below. More notifications may be added in the future. You can find notification keys in this code: https://github.com/openedx/edx-platform/blob/2aeac459945e3e11c153fdb5203ea020514548d5/openedx/core/djangoapps/notifications/base_notification.py#L66

| # | Notification app | Notification key | is_core True? | Appears on Account Settings page as |
|---|------------------|------------------|---------------|-------------------------------------|
| 1 | discussion | new_response | Yes | Activity Notifications |
| 2 | discussion | new_comment | Yes | Activity Notifications |
| 3 | discussion | new_comment_on_response | Yes | Activity Notifications |
| 4 | discussion | response_on_followed_post | Yes | Activity Notifications |
| 5 | discussion | comment_on_followed_post | Yes | Activity Notifications |
| 6 | discussion | response_endorsed_on_thread | Yes | Activity Notifications |
| 7 | discussion | response_endorsed | Yes | Activity Notifications |
| 8 | discussion | content_reported | No | Reported content |
| 9 | discussion | new_question_post | No | New question posts |
| 10 | discussion | new_discussion_post | No | New discussion posts |
| 11 | discussion | new_instructor_all_learners_post | No | New posts from instructors |
| 12 | updates | course_updates | No | Course updates |
| 13 | grading | ora_staff_notifications | No | New ORA submission for staff |
| 14 | grading | ora_grade_assigned | No | ORA grade received |

### Example configuration for overriding notification preferences:

```python
NOTIFICATION_TYPES_OVERRIDE = {
    # Turn off tray and and turn on email notifications for new discussion posts and set daily cadence.
    'new_discussion_post': {
        'email': True,
        'web': False,
        'email_cadence': 'Daily',
    },
    # Turn off email notifications for "Course Updates" and prevent users from changing it.
    'course_updates': {
        'email': False,
        'non_editable': ['email'],
    }
}
```

### Example configuration for overriding notification preference marked as core:

```python
NOTIFICATION_APPS_OVERRIDE = {
    # Turn on tray and turn off email for 7 discussion notification types that appear on Account Settings page as "Activity Notifications".
    'discussion': {
        'core_email': False,
        'core_web': True
    }
}
```

### Why isn't my override working?

- See if you are using the exact key name (e.g. `new_discussion_post` and not `New_discussion_post`).
- If a notification is marked as core (`is_core: True`) in the code, it will ignore overrides in `NOTIFICATION_TYPES_OVERRIDE`. You must override using `NOTIFICATION_APPS_OVERRIDE` instead.
