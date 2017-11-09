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

The app measures a learner's progress in a "Schedule" Django object. A Schedule
stores the day a learner enrolls in a course and the learner's "upgrade
deadline" (the date before which they can purchase a verified certificate). The
app coordinates its messaging to learners through their Schedules. 

## Definitions

* Schedule
* Schedule Experience
* Upgrade Deadline
    - May either mean the soft upgrade deadline on the Schedule model or the
      hard experation date for upgrading on the course.
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

### Configuration Models

Make sure a Site has been created at `<lms_url>/admin/sites/site`.

In the Django admin panel at `<lms_url>/admin/schedules/scheduleconfig/` create
a ScheduleConfig and link it to the Site. Make sure to enable all of the
settings:

* `create_schedules`: enables creating new Schedules when new Course Enrollments
  are created.
* `enqueue_*`: allows sending email tasks of this message type to celery.
* `deliver_*`: allows delivering emails through ACE for this message type.
* `hold_back_ratio`: ratio of all new Course Enrollments that should NOT have a
  Schedule created.

If you are testing with a particular course, make sure that it is self-paced by
going to `<studio_url>/admin/self_paced/selfpacedconfiguration/` and add an
enabled self paced config. Then, go to Studio settings for the course and change
the Course Pacing value to "Self-Paced". Note that the Course Start Date has to
be set to sometime in the future in order to change the Course Pacing.

### Waffle Flags and Switches

#### Global

All waffle flags and switches can be created at `<lms_url/admin/waffle/`.

#### Org-level

#### Course-level

Schedule creation: `schedules.create_schedules_for_course`



### Other Requirements

## Testing Changes

### Running in Devstack

The management command?

Outputting to File backend.

### Litmus
