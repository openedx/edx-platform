Survey Report
===============

This Django app was created to gather aggregated, anonymized data about Open edX courses at scale so that we can begin to track the growth and trends in Open edX usage over time, namely in the annual Open edX Impact Report.

With this app, you can collect the following information on your platform:

- ``courses_offered``: Total number of active unique courses.
- ``learners``: Recently active users with login in the last four weeks.
- ``registered_learners``: Total number of users ever registered in the platform.
- ``enrollments``: Total number of active enrollments in the platform.
- ``generated_certificates``: Total number of generated certificates.
- ``extra_data``: Extra information that will be saved in the report, e.g., site_name, openedx-release.
- ``state``: State of the async generating process.

You can find in this directory:
- Some methods to manage survey reports.
- One command to generate the report.
- Some queries to get the information from the database.
- One method to send the report to Open edX API.

How to Generate a Report and Send It
-------------------------------------

By setting ``SURVEY_REPORT_ENDPOINT``, you can choose to whom you would like to send the report; by default, you will send the report to the Open edX organization to collaborate with the annual Open edX Impact Report. You can see `Settings for Survey Report`_ for more information.

.. TODO: Complete this part
    By the tutor plugin X
    ~~~~~~~~~~~~~~~~~~~~~~
    You can generate and send reports automatically by installing the tutor plugin X and following its instructions.

Django Admin
~~~~~~~~~~~~~
You can create reports using the Django Admin; for that, you need to follow these steps:

1. Enter the **Survey Report** option in your Django admin (URL: ``<your LMs domain>/admin/survey_report/surveyreport/``)
2. Click the **Generate Report** button.
3. Then, you can select the reports you want to send and use the admin actions to send the report to an external API.

    .. image:: docs/_images/survey_report_admin.png
        :alt: Survey report by Django admin

Screenshot of Survey Report option in a Django admin and use the admin actions to send the report to an external API

Command Line
~~~~~~~~~~~~~
1. Run a Bash shell in your LMS container. For example, using ``tutor dev run lms bash``.
2. Run the command: ``./manage.py lms generate_report``

**Note:** by default that the command also sends the report; if you only want to generate it, you need to add the flag ``--no-send``. For more information, you can run the command ``./manage.py lms generate_report --help``

    .. image:: docs/_images/survey_report_command.png
        :alt: Survey Report by command line

Screenshot of a bash shell with the result of running ``./manage.py lms generate_report --no-send``

Settings for Survey Report
----------------------------

You have the following settings to customize the behavior of your reports.

- ``SURVEY_REPORT_EXTRA_DATA``: This setting is a dictionary. This info will appear as a value in the report extra_data attribute. By default, the value is {}.

- ``SURVEY_REPORT_ENDPOINT``: This setting is a string with the endpoint to send the report. This URL should be capable of receiving a POST request with the data. By default, the setting is to an Open edX organization endpoint.

- ``ANONYMOUS_SURVEY_REPORT``: This is a boolean to specify if you want to use your LMS domain as ID for your report or to send the information anonymously with a UUID. By default, this setting is False.

- ``SURVEY_REPORT_ENABLE``: This is a boolean to specify if you want to enable or disable the survey report feature completely. The banner will disappear and the report generation will be disabled if set to False. By default, this setting is True.

About the Survey Report Admin Banner
-------------------------------------

This app implements a banner to make it easy for the Open edX operators to generate and send reports automatically.

    .. image:: docs/_images/survey_report_banner.png
        :alt: Survey Report Banner

**Note:** The banner will appear if a survey report is not sent in the months defined in the ``context_processor`` file, by default, is set to appear every 6 months.
