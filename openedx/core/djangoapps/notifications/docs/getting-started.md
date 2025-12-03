# Getting started with notifications

1. You will need to configure `NOTIFICATIONS_DEFAULT_FROM_EMAIL` to send email notifications.
2. Daily and weekly digest emails require the respective management commands to be run on a daily and weekly basis:
   - daily: `manage.py lms send_email_digest Daily`
   - weekly: `manage.py lms send_email_digest Weekly`

    Example crontab entries:

    ```
    0 22 * * * ./manage.py lms send_email_digest Daily
    0 22 * * SUN ./manage.py lms send_email_digest Weekly
    ```
