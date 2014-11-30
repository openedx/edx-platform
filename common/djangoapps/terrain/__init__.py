# Use this as your lettuce terrain file so that the common steps
# across all lms apps can be put in terrain/common
# See https://groups.google.com/forum/?fromgroups=#!msg/lettuce-users/5VyU9B4HcX8/USgbGIJdS5QJ

from terrain.browser import *  # pylint: disable=wildcard-import
from terrain.steps import *  # pylint: disable=wildcard-import
from terrain.factories import *  # pylint: disable=wildcard-import
from terrain.setup_prereqs import *  # pylint: disable=wildcard-import
