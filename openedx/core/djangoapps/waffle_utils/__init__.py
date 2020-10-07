"""
Utilities for waffle.

Includes namespacing, caching, and course overrides for waffle flags.

Usage:

For Waffle Flags, first set up the namespace, and then create flags using the
namespace.  For example::

   WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='my_namespace')

   # Use CourseWaffleFlag when you are in the context of a course.
   SOME_COURSE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'some_course_feature', __name__)
   # Use WaffleFlag when outside the context of a course.
   SOME_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'some_feature', __name__)

You can check these flags in code using the following::

    SOME_FLAG.is_enabled()
    SOME_COURSE_FLAG.is_enabled(course_key)

To test these WaffleFlags, see testutils.py.

In the above examples, you will use Django Admin "waffle" section to configure
for a flag named: my_namespace.some_course_feature

You could also use the Django Admin "waffle_utils" section to configure a course
override for this same flag (e.g. my_namespace.some_course_feature).

For Waffle Switches, first set up the namespace, and then create the flag name.
For example::

    WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

    ESTIMATE_FIRST_ATTEMPTED = 'estimate_first_attempted'

You can then use the switch as follows::

    WAFFLE_SWITCHES.is_enabled(waffle.ESTIMATE_FIRST_ATTEMPTED)

To test WaffleSwitchNamespace, use the provided context managers.  For example:

    with WAFFLE_SWITCHES.override(waffle.ESTIMATE_FIRST_ATTEMPTED, active=True):
        ...

For long-lived flags, you may want to change the default for devstack, sandboxes,
or new Open edX releases. For help with this, see:
openedx/core/djangoapps/waffle_utils/docs/decisions/0001-refactor-waffle-flag-default.rst

Also see ``WAFFLE_FLAG_CUSTOM_ATTRIBUTES`` and docstring for _set_waffle_flag_attribute
for temporarily instrumenting/monitoring waffle flag usage.

"""
from functools import lru_cache
import logging
import re
import traceback
from abc import ABCMeta
from contextlib import contextmanager
from weakref import WeakSet

import crum
from django.conf import settings
from edx_django_utils.monitoring import set_custom_attribute
from opaque_keys.edx.keys import CourseKey
from waffle import flag_is_active, switch_is_active

from openedx.core.lib.cache_utils import get_cache as get_request_cache

from edx_toggles.toggles import BaseNamespace
from edx_toggles.toggles import WaffleSwitch as BaseWaffleSwitch
from edx_toggles.toggles import WaffleSwitchNamespace as BaseWaffleSwitchNamespace

log = logging.getLogger(__name__)


class WaffleSwitchNamespace(BaseWaffleSwitchNamespace):
    """
    A waffle switch namespace class that implements request-based caching.
    """

    @property
    def _cached_switches(self):
        """
        Returns a dictionary of all namespaced switches in the request cache.
        """
        return _get_waffle_namespace_request_cache().setdefault("switches", {})


def _get_waffle_namespace_request_cache():
    """
    Returns a request cache shared by all Waffle namespace objects.
    """
    return get_request_cache("WaffleNamespace")


class WaffleSwitch(BaseWaffleSwitch):
    NAMESPACE_CLASS = WaffleSwitchNamespace


class WaffleFlagNamespace(BaseNamespace):
    """
    Provides a single namespace for a set of waffle flags.

    All namespaced flag values are stored in a single request cache containing
    all flags for all namespaces.
    """

    @property
    def _cached_flags(self):
        """
        Returns a dictionary of all namespaced flags in the request cache.
        """
        return _get_waffle_namespace_request_cache().setdefault("flags", {})

    def is_flag_active(self, flag_name):
        """
        Returns and caches whether the provided flag is active.

        If the flag value is already cached in the request, it is returned.

        Note: A waffle flag's default is False if not defined. If you think you
            need the default to be True, see the module docstring for
            alternatives.

        Arguments:
            flag_name (String): The name of the flag to check.
        """
        namespaced_flag_name = self._namespaced_name(flag_name)
        value = self._get_flag_active(namespaced_flag_name)
        _set_waffle_flag_attribute(namespaced_flag_name, value)
        return value

    def _get_flag_active(self, namespaced_flag_name):
        """
        Return the value of the flag activation without touching the _waffle_flag_attribute.
        """
        # Check namespace cache
        value = self._cached_flags.get(namespaced_flag_name)
        if value is not None:
            return value

        # Check in context of request
        request = crum.get_current_request()
        value = self._get_flag_active_request(namespaced_flag_name, request)
        if value is not None:
            return value

        # Check value in the absence of any context
        log.warning(
            u"%sFlag '%s' accessed without a request",
            self.log_prefix,
            namespaced_flag_name,
        )
        # Return the Flag's Everyone value if not in a request context.
        # Note: this skips the cache as the value might be different
        # in a normal request context. This case seems to occur when
        # a page redirects to a 404, or for celery workers.
        value = is_flag_active_for_everyone(namespaced_flag_name)
        set_custom_attribute("warn_flag_no_request_return_value", value)
        return value

    def _get_flag_active_request(self, namespaced_flag_name, request):
        """
        Get flag value in the context of the current request.
        """
        if request:
            value = flag_is_active(request, namespaced_flag_name)
            self._cached_flags[namespaced_flag_name] = value
            return value
        return None


# .. toggle_name: WAFFLE_FLAG_CUSTOM_ATTRIBUTES
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: A list of waffle flags to track with custom attributes having
#   values of (True, False, or Both).
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2020-06-17
# .. toggle_warnings: Intent is for temporary research (1 day - several weeks) of a flag's usage.
@lru_cache(maxsize=None)
def _get_waffle_flag_custom_attributes_set():
    attributes = getattr(settings, "WAFFLE_FLAG_CUSTOM_ATTRIBUTES", None) or []
    return set(attributes)


def _set_waffle_flag_attribute(name, value):
    """
    For any flag name in settings.WAFFLE_FLAG_CUSTOM_ATTRIBUTES, add name/value
    to cached values and set custom attribute if the value changed.

    The name of the custom attribute will have the prefix ``flag_`` and the
    suffix will match the name of the flag.
    The value of the custom attribute could be False, True, or Both.

    The value Both would mean that the flag had both a True and False
    value at different times during the transaction. This is most
    likely due to having a course override, as is the case with
    CourseWaffleFlag.

    An example NewRelic query to see the values of a flag in different
    environments, if your waffle flag was named ``my.waffle.flag`` might
    look like::

      SELECT count(*) FROM Transaction
      WHERE flag_my.waffle.flag IS NOT NULL
      FACET appName, flag_my.waffle.flag

    Important: Remember to configure ``WAFFLE_FLAG_CUSTOM_ATTRIBUTES`` for
    LMS, Studio and Workers in order to see waffle flag usage in all
    edx-platform environments.
    """
    if name not in _get_waffle_flag_custom_attributes_set():
        return

    flag_attribute_data = _get_waffle_namespace_request_cache().setdefault(
        "flag_attribute", {}
    )
    is_value_changed = True
    if name not in flag_attribute_data:
        # New flag
        flag_attribute_data[name] = str(value)
    else:
        # Existing flag
        if flag_attribute_data[name] == str(value):
            # Same value
            is_value_changed = False
        else:
            # New value
            flag_attribute_data[name] = "Both"

    if is_value_changed:
        attribute_name = "flag_{}".format(name)
        set_custom_attribute(attribute_name, flag_attribute_data[name])


def is_flag_active_for_everyone(namespaced_flag_name):
    """
    Returns True if the waffle flag is configured as active for Everyone,
    False otherwise.
    """
    # Import is placed here to avoid model import at project startup.
    from waffle.models import Flag

    try:
        waffle_flag = Flag.objects.get(name=namespaced_flag_name)
        return waffle_flag.everyone is True
    except Flag.DoesNotExist:
        return False


class WaffleFlag:
    """
    Waffle flag class that implements custom override method.

    This class should be removed in favour of edx_toggles.toggles.WaffleFlag once we get rid of the WaffleFlagNamespace
    class and the `override` method.
    """

    NAMESPACE_CLASS = WaffleFlagNamespace

    # use a WeakSet so these instances can be garbage collected if need be
    _class_instances = WeakSet()

    def __init__(self, waffle_namespace, flag_name, module_name=None):
        """
        Initializes the waffle flag instance.

        Arguments:
            waffle_namespace (WaffleFlagNamespace | String): Namespace for this flag.
            flag_name (String): The name of the flag (without namespacing).
            module_name (String): The name of the module where the flag is created. This should be ``__name__`` in most
            cases.
        """
        if isinstance(waffle_namespace, str):
            waffle_namespace = self.NAMESPACE_CLASS(name=waffle_namespace)

        self.waffle_namespace = waffle_namespace
        self.flag_name = flag_name
        self._module_name = module_name or ""
        self._class_instances.add(self)

    @classmethod
    def get_instances(cls):
        """ Returns a WeakSet of the instantiated instances of WaffleFlag. """
        return cls._class_instances

    @property
    def module_name(self):
        """
        Returns the module name. This is cached to work with the WeakSet instances.
        """
        return self._module_name

    @module_name.setter
    def module_name(self, value):
        self._module_name = value

    @property
    def namespaced_flag_name(self):
        """
        Returns the fully namespaced flag name.
        """
        # pylint: disable=protected-access
        return self.waffle_namespace._namespaced_name(self.flag_name)

    def is_enabled(self):
        """
        Returns whether or not the flag is enabled.
        """
        return self.waffle_namespace.is_flag_active(self.flag_name)

    @contextmanager
    def override(self, active=True):
        """
        Shortcut method for `override_waffle_flag`.
        """
        # TODO We can move this import to the top of the file once this code is
        # not all contained within the __init__ module.
        from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag

        with override_waffle_flag(self, active):
            yield


class CourseWaffleFlag(WaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course.

    Uses a cached waffle namespace.

    Usage:

       WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='my_namespace')
       SOME_COURSE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'some_course_feature', __name__)

    And then we can check this flag in code with::

        SOME_COURSE_FLAG.is_enabled(course_key)

    The Django Admin "waffle_utils" section can be used to configure a course override for this same flag (e.g.
    my_namespace.some_course_feature).
    """

    def _get_course_override_value(self, course_key):
        """
        Returns True/False if the flag was forced on or off for the provided course. Returns None if the flag was not
        overridden.

        Note: Has side effect of caching the override value.

        Arguments:
            course_key (CourseKey): The course to check for override before checking waffle.
        """
        # Import is placed here to avoid model import at project startup.
        from .models import WaffleFlagCourseOverrideModel

        cache_key = "{}.{}".format(self.namespaced_flag_name, str(course_key))
        # pylint: disable=protected-access
        course_override = self.waffle_namespace._cached_flags.get(cache_key)

        if course_override is None:
            course_override = WaffleFlagCourseOverrideModel.override_value(
                self.namespaced_flag_name, course_key
            )
            # pylint: disable=protected-access
            self.waffle_namespace._cached_flags[cache_key] = course_override

        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.on:
            return True
        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.off:
            return False
        return None

    def is_enabled(self, course_key=None):  # pylint: disable=arguments-differ
        """
        Returns whether or not the flag is enabled within the context of a given course.

        Arguments:
            course_key (Optional[CourseKey]): The course to check for override before
                checking waffle. If omitted, check whether the flag is enabled
                outside the context of any course.
        """
        if course_key:
            assert isinstance(
                course_key, CourseKey
            ), "Provided course_key '{}' is not instance of CourseKey.".format(
                course_key
            )
        is_enabled_for_course = self._get_course_override_value(course_key)
        if is_enabled_for_course is not None:
            _set_waffle_flag_attribute(self.namespaced_flag_name, is_enabled_for_course)
            return is_enabled_for_course
        return super().is_enabled()
