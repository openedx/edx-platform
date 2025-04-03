.. _extending-retirement:

Extending The Retirement Pipeline
#################################

Often times Open edX is used in conjunction with other systems. For example, a university may have an email provider that is used to contact students. In this case, it may be desirable to extend the retirement pipeline to include a step that calls the email provider's deletion API when a user is retired in Open edX.

Currently, the retirement code only supports a handful of services (LMS, Ecommerce, Course Discovery, and some historical 3rd party providers) so it is necessary to add your extension point to one of those services or to have a separate process that uses the retirement APIs outside of the pipeline scripts that currently exist.

There are two main ways to extend the retirement pipeline in its current form:

#. Inside the LMS, a Django Signal is emitted when a user is retired. You can create an edx-platform plugin that listens for this signal and take appropriate action from the LMS. The signal is named `USER_RETIRE_LMS_MISC` and it is defined in `openedx.core.djangoapps.user_api.accounts.signals`.

#. Use the retirement APIs to find recently retired users and have an entirely out of band process to propagate them out in the time period between when the user is retired and when the retirement data is completely removed from the system. This would involve using or replicating `utils/edx_api.py`'s LmsApi to find users (ex: `get_learners_by_date_and_status` method to find users in the `COMPLETE` status that were last touched in the last 24 hours). You could then use the returned user data to find the user in the external system and delete them. This method does not provide the same guarantees as the first, but it does allow for more flexibility in the actions that can be taken.
