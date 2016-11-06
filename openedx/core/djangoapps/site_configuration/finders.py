"""
Static file finders for Django.
https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-STATICFILES_FINDERS
Yes, this interface is private and undocumented, but we need to access it anyway.

In order to deploy Open edX in production, it's important to be able to collect
and process static assets: images, CSS, JS, fonts, etc. Django's collectstatic
system is the accepted way to do that in Django-based projects, but that system
doesn't handle every kind of collection and processing that web developers need.
Other open source projects like `Django-Pipeline`_ and `Django-Require`_ hook
into Django's collectstatic system to provide features like minification,
compression, Sass pre-processing, and require.js optimization for assets before
they are pushed to production. To make sure that themed assets are collected
and served by the system (in addition to core assets), we need to extend this
interface, as well.

.. _Django-Pipeline: http://django-pipeline.readthedocs.org/
.. _Django-Require: https://github.com/etianen/django-require
"""

from django.conf import settings
from django.contrib.staticfiles.finders import AppDirectoriesFinder


class AppDirectoriesTemplateFinder(AppDirectoriesFinder):
    """
    A static files finder that looks in the templates/ directory of each app.

    This is a temporary measure to ease refactoring templates into app
    directories.  As that work is done
    """
    source_dir = u'templates'

    def __init__(self, *args, **kwargs):
        # provide a fake app name if no apps are provided, because if the
        # superclass receives an empty set, it will process all apps instead of
        # no apps.
        app_names = getattr(settings, 'APPS_WITH_STATICFILES_IN_TEMPLATES_DIRECTORY', {u'not an app name!'})
        super(AppDirectoriesTemplateFinder, self).__init__(app_names=app_names, *args, **kwargs)
