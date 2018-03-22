"""
Celery needs to be loaded when the cms modules are so that task
registration and discovery can work correctly.
"""
from __future__ import absolute_import

# We monkey patch Kombu's entrypoints listing because scanning through this
# accounts for the majority of LMS/Studio startup time for tests, and we don't
# use custom Kombu serializers (which is what this is for). Still, this is
# pretty evil, and should be taken out when we update Celery to the next version
# where it looks like this method of custom serialization has been removed.
#
# FWIW, this is identical behavior to what happens in Kombu if pkg_resources
# isn't available.
import kombu.utils
kombu.utils.entrypoints = lambda namespace: iter([])

# Monkey Patch for Django migrations running slow, remove after upgrading to 1.9+
# taken from: https://github.com/cfpb/cfgov-refresh/commit/7616c6bb3ec310e72b1c9538d9176ba61a73ebd3#diff-dffeeb550eca65d51cda43001ff38d4d
import lms.monkey_patch

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import APP as CELERY_APP
