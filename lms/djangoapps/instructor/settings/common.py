"""Common environment variables unique to the instructor plugin."""


from django.utils.translation import ugettext_lazy as _


def plugin_settings(settings):
    """Settings for the instructor plugin."""
    ### Analytics Dashboard (Insights) settings
    settings.ANALYTICS_DASHBOARD_URL = ""
    settings.ANALYTICS_DASHBOARD_NAME = _('Your Platform Insights')
    settings.FEATURES.update({
        # Enable display of enrollment counts in instructor dash, analytics section
        'DISPLAY_ANALYTICS_ENROLLMENTS': True,

        # Display the 'Analytics' tab in the instructor dashboard for CCX courses.
        # Note: This has no effect unless ANALYTICS_DASHBOARD_URL is already set,
        #       because without that setting, the tab does not show up for any courses.
        'ENABLE_CCX_ANALYTICS_DASHBOARD_URL': False,

        # Disable instructor dash buttons for downloading course data
        # when enrollment exceeds this number
        'MAX_ENROLLMENT_INSTR_BUTTONS': 200,

        # Grade calculation started from the instructor dashboard will write grades
        # CSV files to the configured storage backend and give links for downloads.
        'ENABLE_GRADE_DOWNLOADS': False,

        # Give course staff unrestricted access to grade downloads (if set to False,
        # only edX superusers can perform the downloads)
        'ALLOW_COURSE_STAFF_GRADE_DOWNLOADS': False,

        # Show a section in the membership tab of the instructor dashboard
        # to allow an upload of a CSV file that contains a list of new accounts to create
        # and register for course.
        'ALLOW_AUTOMATED_SIGNUPS': False,

        # Batch-Generated Certificates from Instructor Dashboard
        'CERTIFICATES_INSTRUCTOR_GENERATION': False,

        # Whether to check the "Notify users by email" checkbox in the batch enrollment form
        # in the instructor dashboard.
        'BATCH_ENROLLMENT_NOTIFY_USERS_DEFAULT': True,
    })
