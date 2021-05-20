Django Oauth Toolkit Templates
------------------------------

This Django app exists solely to provide a home for the ``authorize.html`` template. This overrides the default version of the template defined in the ``django-oauth-toolkit`` library.

In an ideal world, this template would live in the ``oauth_dispatch`` djangoapp along with our other oauth2 code. Unfortunately, due to `the way that Django's app_directories loader works`_, we cannot put this template
in ``oauth_dispatch``, because the `template defined in django-oauth-toolkit`_ will take precedence over the one in ``oauth_dispatch``. The library must be defined first in ``INSTALLED_APPS``.

So until we find another solution, this template will continue to live here.


.. _the way that Django's app_directories loader works: https://docs.djangoproject.com/en/2.2/ref/templates/api/#django.template.loaders.app_directories.Loader
.. _template defined in the django-oauth-toolkit: https://github.com/jazzband/django-oauth-toolkit/blob/master/oauth2_provider/templates/oauth2_provider/authorize.html
