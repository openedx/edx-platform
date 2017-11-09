# Dynamic Pacing Schedules

The Schedules app allows course teams to automatically email learners taking
self-paced courses. The emails are designed to keep learners engaged with a
course's content. The app sends them at important milestones in a learner's
progression. The app sends three message types "out of the box":

 - Recurring Nudges 
 - Upgrade Reminders 
 - Weekly Course Highlight Messages

Recurring Nudges encourage learners to engage with self-paced courses at regular
intervals.  The app sends learners nudges three days, 10 days, and 19 days after
they enroll in a self-paced course.

Upgrade Reminders signal learners to upgrade to a self-paced course's "Verified"
track. They are sent 19 days from a learner's enrollment date, or two days from
the course's end date.

Weekly Course Highlight Messages tell learners what to look forward to in a
coming week of a course. The app generates messages with instructor-supplied
"section highlights" in the body of the message.

The app measures a learner's progress with a "Schedule" Django object. The app
assigns Schedules to learners and coordinates its messaging with their
Schedules. 

## Glossary

* Schedule 
Stores the day a learner enrolls in a course and the
learner's "upgrade deadline" 

* Schedule Experience

* Upgrade Deadline 

The date before which a learner can purchase a verified certificate. A Schedule
imposes a "soft" upgrade deadline 21 days from when a learner enrolled in a
course. A self-paced course imposes a "hard" upgrade deadline that is the
course-wide expiration date for upgrading on the course. A learner's Schedule
will use whichever date is earlier.

* Recurring Nudge
* Upgrade Reminder
* Course Update
* Highlights
* Resolver
* Task


## User-flow

When a user enrolls in a self-paced course and the necessary flags and
configurations are enabled, a Schedule and ScheduleExperience is created for
them. The Schedule has an upgrade deadline set for some number of days from the
enrollment date.

## Getting Started

These instructions assume you have already setup an Open edX instance or have a
Running devstack. See the [Open edX Developer's
Guide](http://edx.readthedocs.io/projects/edx-developer-guide/en/latest/) for
information on how to set those up.

### Setting up edX Automated Communication Engine (A.C.E.)

The Schedule app relies on ACE, which requires a
[Sailthru](http://www.sailthru.com/) back-end for sending emails. See the
[edx-ace
documentation](https://edx-ace.readthedocs.io/en/latest/getting_started.html#sailthruemailchannel-settings)
for instructions on setting up a Sailthru channel in ACE.

### Django Settings

Edit the `lms.env.json` and add/change the following:

```python
FEATURES = {
    'ENABLE_MKTG_SITE': True,
}
MKTG_URLS = {
    'ROOT': '<insert_lms_url_here>',
}
SOCIAL_MEDIA_FOOTER_URLS = {
    'tumblr': '<insert_tumblr_url_here>',
    'reddit': '<insert_reddit_url_here>',
    'twitter': '<insert_twitter_url_here>',
    'google_plus': '<insert_google_plus_url_here>',
    'youtube': '<insert_youtube_url_here>',
    'linkedin': '<insert_linkedin_url_here>',
    'meetup': '<insert_meetup_url_here>',
    'facebook': '<insert_facebook_url_here>',
}
MOBILE_STORE_URLS = {
    'google': '<insert_play_store_url_here>',
    'apple': '<insert_app_store_url_here>',
}
CONTACT_MAILING_ADDRESS = '<insert_physical_address_here>'
ACE_ENABLED_CHANNEL = ['sailthru_email']
ACE_ENABLED_POLICIES = ['bulk_email_optout']
ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = '<insert_sailthru_template_name_here>'
```

### Configuring Schedule Creation

Make sure a Site has been created at `<lms_url>/admin/sites/site`.

#### ScheduleConfig

In the Django admin panel at `<lms_url>/admin/schedules/scheduleconfig/` create
a ScheduleConfig and link it to the Site. Make sure to enable all of the
settings:

* `create_schedules`: enables creating new Schedules when new Course Enrollments
  are created.
* `hold_back_ratio`: ratio of all new Course Enrollments that should NOT have a
  Schedule created.

#### Roll-out Waffle Flag

There is one roll-out related course waffle flag that we plan to delete called
`schedules.create_schedules_for_course`, which, if the
`ScheduleConfig.create_schedules` is disabled, will enable schedule creation on
a per-course basis.

#### Self-paced Configuration

Schedules will only be created for a course if it is self-paced. A course can be
configured to be self-paced by going to
`<studio_url>/admin/self_paced/selfpacedconfiguration/` and adding an enabled
self paced config. Then, go to Studio settings for the course and change the
Course Pacing value to "Self-Paced". Note that the Course Start Date has to be
set to sometime in the future in order to change the Course Pacing.

### Configuring Upgrade Deadline on Schedule

The upgrade reminder message type depends on there being a date in the
`upgrade_deadline` field of the Schedule model. Up-sell messaging will also be
added to the recurring nudge and course updates message types when an upgrade
deadline date is present.

#### DynamicUpgradeDeadlineConfiguration models

In order to enable filling in the `upgrade_deadline` field of new Schedule
models created, you must create and enable one of the following:

* A DynamicUpgradeDeadlineConfiguration toggles the feature for all courses
  globally.
* A OrgDynamicUpgradeDeadlineConfiguration toggles the feature for all courses
  in a particular organization.
* A CourseDynamicUpgradeDeadlineConfiguration toggles the feature for a
  particular course.

The CourseDynamicUpgradeDeadlineConfiguration takes precedence over the
OrgDynamicUpgradeDeadlineConfiguration which takes precedence over the global
DynamicUpgradeDeadlineConfiguration.

The "deadline days" field specifies how many days from the day of the learner's
enrollment will be their soft upgrade deadline on the Schedule model.

#### Verified Course Mode

The `upgrade_deadline` will only be filled for a course if it has a verified
course mode. To add a verified course mode to a course, go to
`<lms_url>/admin/course_modes/coursemode/` and add a course mode linked with
the course with the "Mode" equal to "verified".

### Configuring Email Sending

#### ScheduleConfig

The ScheduleConfig model at `<lms_url>/admin/schedules/scheduleconfig/` also has
fields which configure enqueueing and delivering emails per message type:

* `enqueue_*`: allows sending email tasks of this message type to celery.
* `deliver_*`: allows delivering emails through ACE for this message type.

#### Roll-out Waffle Flag

Another roll-out related course waffle flag that we plan to delete called
`schedules.send_updates_for_course` will enable sending specifically the course
updates email per-course.

### Configuring Highlights UI in Studio

The button and modal on the course outline page that allows course authors to
enter section highlights can be toggled globally by going to
`<lms_url>/admin/waffle/switch/` and adding an active switch called
`dynamic_pacing.studio_course_update`.

This is a roll-out related waffle switch that we will eventually delete.

### Configuring a Learner's Schedule

Emails will only be sent to learners who have Schedule `start_date`s or
`upgrade_deadline`s and ScheduleExperience that match the criteria for the
message type.

#### Recurring Nudge

* Learners must have the ScheduleExperience type of "Recurring Nudge and Upgrade
Reminder".
* Their Schedule `start_date` must be 3 or 10 days before the current date.

#### Upgrade Reminder

* Learners must have the ScheduleExperience type of "Recurring Nudge and Upgrade
Reminder".
* Their Schedule `upgrade_deadline` must be 2 days after the current date.

#### Course Update

* Learners must have the ScheduleExperience type of "Course Updates".
* Their Schedule `start_date` must be 7, 14, or any increment of 7 days up to 77
  days before the current date.

## Testing Changes

### Running in Devstack

The management command?

Outputting to File backend.

### Litmus
