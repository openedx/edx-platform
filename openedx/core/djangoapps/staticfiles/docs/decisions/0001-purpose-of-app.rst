Purpose of this app: staticfiles
################################

Status
******

**Accepted**


Context
*******

Django provides the ``collectstatic`` management command, which collects static assets into the ``STATIC_ROOT`` so that they can be served by some system external to Django (like nginx or caddy), as is usually desired in production environments.

edx-platform contains several types of files that we don't want to be collected into the ``STATIC_ROOT``. Previously, these files had to be supplied to the management command using the ``--ignore`` option::

    ./manage.py lms collectstatic --ignore geoip --ignore sass ...etc
    ./manage.py cms collectstatic --ignore geoip --ignore sass ...etc

This yields a long, hard-to-remember command. Paver wrapped the command in its big ``paver update_assets`` task, but that task also builds assets, which is totally overkill when you're just trying to collect them.

Fortunately, ``collectstatic``'s default ignore patterns can be configured by defining a custom AppConfig class.

Decision
********

In this app, we define such an config (``EdxPlatformStaticFilesConfig``) for LMS and CMS. Now, devs can collect LMS & CMS assets with just::

    ./manage.py lms collectstatic
    ./manage.py cms collectstatic

Going forward, this app could be used to further customize the Django staticfiles app, although at time of writing no further customizations are planned.

Although the current guidance is to avoid creating new edx-platform apps, there is no other way to add this configuration to the platform. Because the ignore patterns are highly specific to edx-platform, creating this app as a separate library would not be useful.

Further reading
***************

Django's ``collecstatic`` ignore behavior: https://docs.djangoproject.com/en/3.2/ref/contrib/staticfiles/#customizing-the-ignored-pattern-list

Why we are moving away from Paver wrappers: https://github.com/openedx/edx-platform/blob/master/docs/decisions/0017-reimplement-asset-processing.rst

Issue: https://github.com/openedx/edx-platform/issues/31658
