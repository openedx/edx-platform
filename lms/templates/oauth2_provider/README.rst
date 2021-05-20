Django Oauth Toolkit Templates
------------------------------

In an ideal world, these templates would live in the ``oauth_dispatch`` djangoapp along
with our other oauth2 code. Unfortunately, this template is defined within the
``django-oauth-toolkit`` library, which also defines its own version of the template.

Due to `the way that Django's app_directories loader works`_, we cannot put this template
in ``oauth_dispatch``, becuase the `template defined in the library`_ will take precendence
over the one in ``oauth_dispatch``. The library must be defined first in ``INSTALLED_APPS``.

So until we find another solution, this template will continue to live here.


.. _the way that Django's app_directories loader works: https://docs.djangoproject.com/en/2.2/ref/templates/api/#django.template.loaders.app_directories.Loader
.. _template defined in the django-oauth-toolkit: https://github.com/jazzband/django-oauth-toolkit/blob/master/oauth2_provider/templates/oauth2_provider/authorize.html
