.. _settings:

Settings
========

As a `Django project <https://docs.djangoproject.com/>`__, the behaviour of most edx-platform components can be customised via `settings <https://docs.djangoproject.com/en/latest/topics/settings/>`__. However, edx-platform differs from most other Django projects in that it uses *many* different settings (a couple hundred).

The settings for the LMS and the CMS are stored in the `edx-platform/lms/envs <https://github.com/edx/edx-platform/tree/master/lms/envs>`__ and `edx-platform/cms/envs <https://github.com/edx/edx-platform/tree/master/lms/envs>`__ folders. These settings files inherit from one another as follows::
    
    common.py
        ↳ production.py
            ↳ devstack_docker.py

For instance, at the top of ``production.py``, there is::
    
    from .common import *
    # production.py then proceeds to override many of the common settings

To view the value of a particular setting, run::

    ./manage.py lms shell --command \
        "from django.conf import settings; print(settings.SETTINGNAME)"

.. toctree::
   :maxdepth: 2
   
   lms
   cms
