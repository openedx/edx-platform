# Use this as your lettuce terrain file so that the common steps
# across all lms apps can be put in terrain/common
# See https://groups.google.com/forum/?fromgroups=#!msg/lettuce-users/5VyU9B4HcX8/USgbGIJdS5QJ

import lettuce
from django.utils.functional import SimpleLazyObject
from .browser import *  # pylint: disable=wildcard-import
from .factories import absorb_factories
from .steps import *  # pylint: disable=wildcard-import
from .setup_prereqs import *  # pylint: disable=wildcard-import

# Delay absorption of factories until the next access,
# after Django apps have finished initializing
setattr(lettuce, 'world', SimpleLazyObject(absorb_factories))
