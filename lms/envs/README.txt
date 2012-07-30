Transitional for moving to new settings scheme.

To use:
   rake lms
   or
   django-admin.py runserver --settings=lms.envs.dev --pythonpath=.

NOTE: Using manage.py will automatically run mitx/settings.py first, regardless
of what you send it for an explicit --settings flag. It still works, but might
have odd side effects. Using django-admin.py avoids that problem.
django-admin.py is installed by default when you install Django.

To use with gunicorn_django in debug mode:

  gunicorn_django lms/envs/dev.py

