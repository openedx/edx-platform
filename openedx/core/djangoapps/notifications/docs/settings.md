# Notification Configuration Guide

This guide explains how to override default notification settings for the platform without modifying the core code base. You can customize delivery channels (Web, Email) and behavior for specific notification types or entire notification apps using your Django settings.

## Overview

The notification system consists of two main components:

1. **Notification Types**: Specific events (e.g., "New comment on your post", "Grade received").
2. **Notification Apps**: Groups of related notifications (e.g., "Discussions", "Grading").

You can override defaults for both using the django settings:

* `NOTIFICATION_TYPES_OVERRIDE`
* `NOTIFICATION_APPS_OVERRIDE`

---

## 1. Overriding Notification Types

Use `NOTIFICATION_TYPES_OVERRIDE` to change delivery defaults for specific events.

### Allowed Overrides

You can only modify the following fields for a notification type. Any other fields (like templates or triggers) are protected and cannot be changed via settings.

| Key | Type | Description |
| --- | --- | --- |
| `web` | `bool` | Enable/Disable in-browser notifications. |
| `email` | `bool` | Enable/Disable email delivery. |
| `push` | `bool` | Enable/Disable push notifications. |
| `non_editable` | `list` | Prevent users from changing preferences for these channels. |
| `email_cadence` | `str` or `EmailCadence` | How often emails are sent. Allowed values: `Daily`, `Weekly`, `Immediately`, `Never` (or use the `EmailCadence` enum constants).

### Example Configuration

In your `settings.py` (or equivalent):

```python
NOTIFICATION_TYPES_OVERRIDE = {
    # Disable emails for new discussion posts by default and set daily cadence
    'new_discussion_post': {
        'email': False,
        'web': True,
        'email_cadence': 'Daily',
    },

    # Force "Course Updates" to be strictly email-only and deliver immediately
    'course_updates': {
        'email': True,
        'web': False,
        'non_editable': ['email'],
        'email_cadence': 'Immediately',
    }
}

```

### Common Notification Types

| ID | Description | Default Channels |
| --- | --- | --- |
| `new_comment` | A reply to your post. | Web, Email |
| `course_updates` | Announcements from course staff. | Web, Email |
| `ora_grade_assigned` | Grade received on an Open Response Assessment. | Web, Email |
| `content_reported` | Content flagged for moderation. | Web, Email |

---

## 2. Overriding Notification Apps

Use `NOTIFICATION_APPS_OVERRIDE` to change defaults for "Core" notifications. Many notification types are marked as `is_core: True`, meaning they inherit their settings from the App configuration rather than the individual Type configuration.

### Allowed Overrides

These keys affect all "Core" notifications belonging to the app.

| Key | Type | Description |
| --- | --- | --- |
| `core_web` | `bool` | Enable/Disable web delivery for core events. |
| `core_email` | `bool` | Enable/Disable email delivery for core events. |
| `core_push` | `bool` | Enable/Disable push delivery for core events. |
| `non_editable` | `list` | Channels users cannot modify (e.g., `['email']`). |
| `core_email_cadence` | `str` or `EmailCadence` | Default email cadence for core notifications. Allowed values: `Daily`, `Weekly`, `Immediately`, `Never` (or use the `EmailCadence` enum constants).

### Example Configuration

```python
NOTIFICATION_APPS_OVERRIDE = {
    # Make all Discussion core notifications Web-only and weekly cadence
    'discussion': {
        'core_email': False,
        'core_web': True,
        'core_email_cadence': 'Weekly',
    },

    # Ensure Grading core notifications are always delivered via email immediately
    # and users cannot disable them.
    'grading': {
        'core_email': True,
        'non_editable': ['email'],
        'core_email_cadence': 'Immediately',
    }
}

```

### Available Apps

* `discussion`: Handles all forum interactions (replies, threads, comments).
* `grading`: Handles ORA (Open Response Assessment) submissions and grades.
* `updates`: Handles course-wide announcements.

---

## Troubleshooting

**Why isn't my override working?**

1. **Check the Key Name:** Ensure you are using the exact ID (e.g., `new_discussion_post`, not `New Discussion Post`).
2. **Check for "Core" Status:** If a notification is defined as `is_core: True` in the code, it will ignore overrides in `NOTIFICATION_TYPES_OVERRIDE` regarding channels (`web`, `email`). You must override the parent **App** in `NOTIFICATION_APPS_OVERRIDE` instead.
