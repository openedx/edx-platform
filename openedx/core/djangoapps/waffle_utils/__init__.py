"""
Utilities for waffle.

Includes namespacing, caching, and course overrides for waffle flags.

Usage:

For Waffle Flags, first set up the namespace, and then create flags using the
namespace.  For example:

   WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

   # Use CourseWaffleFlag when you are in the context of a course.
   UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'unified_course_tab')
   # Use WaffleFlag when outside the context of a course.
   HIDE_SEARCH_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'hide_search')

You can check these flags in code using the following:

    HIDE_SEARCH_FLAG.is_enabled()
    UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key)

To test these WaffleFlags, see testutils.py.

In the above examples, you will use Django Admin "waffle" section to configure
for a flag named: course_experience.unified_course_tab

You could also use the Django Admin "waffle_utils" section to configure a course
override for this same flag (e.g. course_experience.unified_course_tab).

For Waffle Switches, first set up the namespace, and then create the flag name.
For example:

    WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

    ESTIMATE_FIRST_ATTEMPTED = 'estimate_first_attempted'

You can then use the switch as follows:

    WAFFLE_SWITCHES.is_enabled(waffle.ESTIMATE_FIRST_ATTEMPTED)

To test WaffleSwitchNamespace, use the provided context managers.  For example:

    with WAFFLE_SWITCHES.override(waffle.ESTIMATE_FIRST_ATTEMPTED, active=True):
        ...

"""
import logging
from abc import ABCMeta
from contextlib import contextmanager
from opaque_keys.edx.keys import CourseKey
from request_cache import get_cache as get_request_cache, get_request
from waffle import flag_is_active, switch_is_active
from waffle.models import Flag
from waffle.testutils import override_switch as waffle_override_switch

from .models import WaffleFlagCourseOverrideModel

log = logging.getLogger(__name__)


class WaffleNamespace(object):
    """
    A base class for a request cached namespace for waffle flags/switches.

    An instance of this class represents a single namespace
    (e.g. "course_experience"), and can be used to work with a set of
    flags or switches that will all share this namespace.
    """
    __metaclass__ = ABCMeta

    def __init__(self, name, log_prefix=None):
        """
        Initializes the waffle namespace instance.

        Arguments:
            name (String): Namespace string appended to start of all waffle
                flags and switches (e.g. "grades")
            log_prefix (String): Optional string to be appended to log messages
                (e.g. "Grades: "). Defaults to ''.

        """
        assert name, "The name is required."
        self.name = name
        self.log_prefix = log_prefix if log_prefix else ''

    def _namespaced_name(self, setting_name):
        """
        Returns the namespaced name of the waffle switch/flag.

        For example, the namespaced name of a waffle switch/flag would be:
            my_namespace.my_setting_name

        Arguments:
            setting_name (String): The name of the flag or switch.
        """
        return u'{}.{}'.format(self.name, setting_name)

    @staticmethod
    def _get_request_cache():
        """
        Returns a request cache shared by all instances of this class.
        """
        return get_request_cache('WaffleNamespace')


class WaffleSwitchNamespace(WaffleNamespace):
    """
    Provides a single namespace for a set of waffle switches.

    All namespaced switch values are stored in a single request cache containing
    all switches for all namespaces.
    """
    def is_enabled(self, switch_name):
        """
        Returns and caches whether the given waffle switch is enabled.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        value = self._cached_switches.get(namespaced_switch_name)
        if value is None:
            value = switch_is_active(namespaced_switch_name)
            self._cached_switches[namespaced_switch_name] = value
        return value

    @contextmanager
    def override(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the request cache AND in the model.
        """
        previous_active = self.is_enabled(switch_name)
        try:
            self.override_for_request(switch_name, active)
            with self.override_in_model(switch_name, active):
                yield
        finally:
            self.override_for_request(switch_name, previous_active)

    def override_for_request(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the remainder of
        this request (as this is not a context manager).
        Note: The value is overridden in the request cache, not in the model.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        self._cached_switches[namespaced_switch_name] = active
        log.info(u"%sSwitch '%s' set to %s for request.", self.log_prefix, namespaced_switch_name, active)

    @contextmanager
    def override_in_model(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the model, not the request cache.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        with waffle_override_switch(namespaced_switch_name, active):
            log.info(u"%sSwitch '%s' set to %s in model.", self.log_prefix, namespaced_switch_name, active)
            yield

    @property
    def _cached_switches(self):
        """
        Returns a dictionary of all namespaced switches in the request cache.
        """
        return self._get_request_cache().setdefault('switches', {})


class WaffleFlagNamespace(WaffleNamespace):
    """
    Provides a single namespace for a set of waffle flags.

    All namespaced flag values are stored in a single request cache containing
    all flags for all namespaces.
    """
    __metaclass__ = ABCMeta

    @property
    def _cached_flags(self):
        """
        Returns a dictionary of all namespaced flags in the request cache.
        """
        return self._get_request_cache().setdefault('flags', {})

    def is_flag_active(self, flag_name, check_before_waffle_callback=None, flag_undefined_default=None):
        """
        Returns and caches whether the provided flag is active.

        If the flag value is already cached in the request, it is returned.
        If check_before_waffle_callback is supplied, it is called before
            checking waffle.
        If check_before_waffle_callback returns None, or if it is not supplied,
            then waffle is used to check the flag.

        Arguments:
            flag_name (String): The name of the flag to check.
            check_before_waffle_callback (function): (Optional) A function that
                will be checked before continuing on to waffle. If
                check_before_waffle_callback(namespaced_flag_name) returns True
                or False, it is cached and returned.  If it returns None, then
                waffle is used.
            flag_undefined_default (Boolean): A default value to be returned if
                the waffle flag is to be checked, but doesn't exist.
        """
        # validate arguments
        namespaced_flag_name = self._namespaced_name(flag_name)
        value = self._cached_flags.get(namespaced_flag_name)

        if value is None:
            if check_before_waffle_callback:
                value = check_before_waffle_callback(namespaced_flag_name)

            if value is None:

                if flag_undefined_default is not None:
                    # determine if the flag is undefined in waffle
                    try:
                        Flag.objects.get(name=namespaced_flag_name)
                    except Flag.DoesNotExist:
                        value = flag_undefined_default

                if value is None:
                    value = flag_is_active(get_request(), namespaced_flag_name)

            self._cached_flags[namespaced_flag_name] = value
        return value


class WaffleFlag(object):
    """
    Represents a single waffle flag, using a cached waffle namespace.
    """

    def __init__(self, waffle_namespace, flag_name, flag_undefined_default=None):
        """
        Initializes the waffle flag instance.

        Arguments:
            waffle_namespace (WaffleFlagNamespace): Provides a cached namespace
                for this flag.
            flag_name (String): The name of the flag (without namespacing).
            flag_undefined_default (Boolean): A default value to be returned if
                the waffle flag is to be checked, but doesn't exist.
        """
        self.waffle_namespace = waffle_namespace
        self.flag_name = flag_name
        self.flag_undefined_default = flag_undefined_default

    def is_enabled(self):
        """
        Returns whether or not the flag is enabled.
        """
        return self.waffle_namespace.is_flag_active(
            self.flag_name,
            flag_undefined_default=self.flag_undefined_default
        )


class CourseWaffleFlag(WaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course.

    Uses a cached waffle namespace.
    """

    def _get_course_override_callback(self, course_id):
        """
        Returns a function to use as the check_before_waffle_callback.

        Arguments:
            course_id (CourseKey): The course to check for override before
            checking waffle.
        """
        def course_override_callback(namespaced_flag_name):
            """
            Returns True/False if the flag was forced on or off for the provided
            course.  Returns None if the flag was not overridden.

            Arguments:
                namespaced_flag_name (String): A namespaced version of the flag
                    to check.
            """
            force_override = WaffleFlagCourseOverrideModel.override_value(namespaced_flag_name, course_id)

            if force_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.on:
                return True
            if force_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.off:
                return False
            return None
        return course_override_callback

    def is_enabled(self, course_key=None):
        """
        Returns whether or not the flag is enabled.

        Arguments:
            course_key (CourseKey): The course to check for override before
            checking waffle.
        """
        # validate arguments
        assert issubclass(type(course_key), CourseKey), "The course_id '{}' must be a CourseKey.".format(
            str(course_key)
        )

        return self.waffle_namespace.is_flag_active(
            self.flag_name,
            check_before_waffle_callback=self._get_course_override_callback(course_key),
            flag_undefined_default=self.flag_undefined_default
        )
