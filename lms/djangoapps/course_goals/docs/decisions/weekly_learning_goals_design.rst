Weekly learning goals design
=============================

Status
======

Accepted

Context
=======

Weekly learning goals is a feature that allows users to set a per-course learning goal and sends users goal reminder emails.
You can see more details about the feature here. 
https://openedx.atlassian.net/wiki/spaces/ENGAGE/pages/3242164244/Weekly+Learning+Goals

Decisions
=========

#. **Open-source compatability** - We considered using braze to build the email itself and using a segment webhook to populate user activity. However, this would add a dependency on both braze and segment, which would make this feature incompatible with open source installations. Instead, the email is built with edx-ace and user activity is populated by hooking into our backend APIs in platform.

#. **Storing user activity** - We decided to just store a single row per day per course for user activity. We considered storing more data that might be useful for future features; however, we didn't want this table to grow too big very quickly, so we stored the minimum we need for just this feature - we can always store additional data in the future if we need it. We also considered using the user activity data from our data pipeline, but this wouldn't be easy to use for in-platform features and wouldn't be open source friendly.

#. **Unsubscribing** - We wanted to enable users to unsubscribe from these emails, but to keep the subscription settings in sync with our subscribed_to_goal_reminders setting in platform, we are using a custom unsubscribe link - and this email ignores the subscription settings for other braze emails.

#. **Days and Timezones** - We chose to count a week of user activity from Monday to Sunday to keep things simple. We start counting user activity at midnight based on the user's timezone or last seen timezone if a timezone is not set.
