Site Configuration
==================

These are the site configuration flags that affect Credentials features.

ENABLE_LEARNER_RECORDS
----------------------

Controls whether the LMS integrates with the Learner Records feature in Credentials. Specifically, this turns on some web buttons that link to a learner's record on the Credentials IDA and enables some data being passed to Credentials related to those records.

If you have had this disabled and decide to enable it, you will need to backpopulate the data that was not sent while the feature was disabled. Look into running the ``notify_credentials`` management command.

Note that Credentials has a similar site config option that you'll want to keep in sync with this setting.

Default is ``True``.
