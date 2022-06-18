"""
Deprecated OpaqueKey implementations used by XML and Mongo modulestores
"""

import re
import warnings

from opaque_keys.edx.keys import i4xEncoder as real_i4xEncoder
from opaque_keys.edx.locator import AssetLocator, BlockUsageLocator, CourseLocator, Locator


# This file passes through to protected members of the non-deprecated classes,
# and that's ok. It also may not implement all of the current UsageKey methods.
# pylint: disable=protected-access, abstract-method


class i4xEncoder(real_i4xEncoder):  # pylint: disable=invalid-name
    """Deprecated. Use :class:`keys.i4xEncoder`"""

    def __init__(self, *args, **kwargs):
        """Deprecated. Use :class:`keys.i4xEncoder.default`"""
        warnings.warn(
            "locations.i4xEncoder.default is deprecated! Please use keys.i4xEncoder.default",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class SlashSeparatedCourseKey(CourseLocator):
    """Deprecated. Use :class:`locator.CourseLocator`"""
    def __init__(self, org, course, run, **kwargs):
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use locator.CourseLocator",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(org, course, run, deprecated=True, **kwargs)

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use :meth:`locator.CourseLocator.from_string`."""
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use locator.CourseLocator",
            DeprecationWarning,
            stacklevel=2
        )
        return CourseLocator.from_string(serialized)

    def replace(self, **kwargs):
        """
        Return: a new :class:`SlashSeparatedCourseKey` with specific ``kwargs`` replacing
            their corresponding values.

        Using CourseLocator's replace function results in a mismatch of __init__ args and kwargs.
            Replace tries to instantiate a SlashSeparatedCourseKey object with CourseLocator args and kwargs.
        """
        # Deprecation value is hard coded as True in __init__ and therefore does not need to be passed through.
        return SlashSeparatedCourseKey(
            kwargs.pop('org', self.org),
            kwargs.pop('course', self.course),
            kwargs.pop('run', self.run),
            **kwargs
        )


class LocationBase:
    """Deprecated. Base class for :class:`Location` and :class:`AssetLocation`"""

    DEPRECATED_TAG = None  # Subclasses should define what DEPRECATED_TAG is

    @classmethod
    def _deprecation_warning(cls):
        """Display a deprecation warning for the given cls"""
        if issubclass(cls, Location):
            warnings.warn(
                "Location is deprecated! Please use locator.BlockUsageLocator",
                DeprecationWarning,
                stacklevel=3
            )
        elif issubclass(cls, AssetLocation):
            warnings.warn(
                "AssetLocation is deprecated! Please use locator.AssetLocator",
                DeprecationWarning,
                stacklevel=3
            )
        else:
            warnings.warn(
                f"{cls} is deprecated!",
                DeprecationWarning,
                stacklevel=3
            )

    @property
    def tag(self):
        """Deprecated. Returns the deprecated tag for this Location."""
        warnings.warn(
            "Tag is no longer supported as a property of Locators.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.DEPRECATED_TAG

    @classmethod
    def _check_location_part(cls, val, regexp):
        """Deprecated. See CourseLocator._check_location_part"""
        cls._deprecation_warning()
        return CourseLocator._check_location_part(val, regexp)

    @classmethod
    def _clean(cls, value, invalid):
        """Deprecated. See BlockUsageLocator._clean"""
        cls._deprecation_warning()
        return BlockUsageLocator._clean(value, invalid)

    @classmethod
    def clean(cls, value):
        """Deprecated. See BlockUsageLocator.clean"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean(value)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """Deprecated. See BlockUsageLocator.clean_keeping_underscores"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_keeping_underscores(value)

    @classmethod
    def clean_for_url_name(cls, value):
        """Deprecated. See BlockUsageLocator.clean_for_url_name"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_for_url_name(value)

    @classmethod
    def clean_for_html(cls, value):
        """Deprecated. See BlockUsageLocator.clean_for_html"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_for_html(value)

    def __init__(self, org, course, run, category, name, revision=None, **kwargs):
        self._deprecation_warning()

        course_key = kwargs.pop('course_key', CourseLocator(
            org=org,
            course=course,
            run=run,
            branch=revision,
            deprecated=True
        ))
        super().__init__(course_key, category, name, deprecated=True, **kwargs)

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use :meth:`locator.BlockUsageLocator.from_string`."""
        cls._deprecation_warning()
        return BlockUsageLocator.from_string(serialized)

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Deprecated. See BlockUsageLocator._from_deprecated_son"""
        cls._deprecation_warning()
        return BlockUsageLocator._from_deprecated_son(id_dict, run)


class Location(LocationBase, BlockUsageLocator):
    """Deprecated. Use :class:`locator.BlockUsageLocator`"""

    DEPRECATED_TAG = 'i4x'

    def replace(self, **kwargs):
        """
        Return: a new :class:`Location` with specific ``kwargs`` replacing
            their corresponding values.

        Using BlockUsageLocator's replace function results in a mismatch of __init__ args and kwargs.
            Replace tries to instantiate a Location object with BlockUsageLocator's args and kwargs.
        """
        #  NOTE: Deprecation value is hard coded as True in __init__ and therefore does not need to be passed through.
        return Location(
            kwargs.pop('org', self.course_key.org),
            kwargs.pop('course', self.course_key.course),
            kwargs.pop('run', self.course_key.run),
            kwargs.pop('category', self.block_type),
            kwargs.pop('name', self.block_id),
            revision=kwargs.pop('revision', self.branch),
            **kwargs
        )


class DeprecatedLocation(BlockUsageLocator):
    """
    The short-lived location:org+course+run+block_type+block_id syntax
    """
    CANONICAL_NAMESPACE = 'location'
    URL_RE_SOURCE = """
        (?P<org>{ALLOWED_ID_CHARS}+)\\+(?P<course>{ALLOWED_ID_CHARS}+)\\+(?P<run>{ALLOWED_ID_CHARS}+)\\+
        (?P<block_type>{ALLOWED_ID_CHARS}+)\\+
        (?P<block_id>{ALLOWED_ID_CHARS}+)
        """.format(ALLOWED_ID_CHARS=Locator.ALLOWED_ID_CHARS)

    URL_RE = re.compile('^' + URL_RE_SOURCE + r'\Z', re.VERBOSE | re.UNICODE)

    def __init__(self, course_key, block_type, block_id):
        if course_key.version_guid is not None:
            raise ValueError("DeprecatedLocations don't support course versions")

        if course_key.branch is not None:
            raise ValueError("DeprecatedLocations don't support course branches")

        super().__init__(course_key, block_type, block_id)

    @classmethod
    def _from_string(cls, serialized):
        """
        see super
        """
        # Allow access to _from_string protected method
        parsed_parts = cls.parse_url(serialized)
        course_key = CourseLocator(
            parsed_parts.get('org'), parsed_parts.get('course'), parsed_parts.get('run'),
            # specifically not saying deprecated=True b/c that would lose the run on serialization
        )
        block_id = parsed_parts.get('block_id')
        return cls(course_key, parsed_parts.get('block_type'), block_id)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = [self.org, self.course, self.run, self.block_type, self.block_id]
        return "+".join(parts)


class AssetLocation(LocationBase, AssetLocator):
    """Deprecated. Use :class:`locator.AssetLocator`"""

    DEPRECATED_TAG = 'c4x'

    def replace(self, **kwargs):
        """
        Return: a new :class:`AssetLocation` with specific ``kwargs`` replacing
            their corresponding values.

        Using AssetLocator's replace function results in a mismatch of __init__ args and kwargs.
            Replace tries to instantiate an AssetLocation object with AssetLocators args and kwargs.
        """
        # NOTE: Deprecation value is hard coded as True in __init__ and therefore does not need to be passed through.
        return AssetLocation(
            kwargs.pop('org', self.org),
            kwargs.pop('course', self.course),
            kwargs.pop('run', self.run),
            kwargs.pop('category', self.block_type),
            kwargs.pop('name', self.block_id),
            revision=kwargs.pop('revision', self.branch),
            **kwargs
        )

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deprecated. See AssetLocator._from_deprecated_string"""
        cls._deprecation_warning()
        return AssetLocator._from_deprecated_string(serialized)

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Deprecated. See BlockUsageLocator._from_deprecated_son"""
        cls._deprecation_warning()
        return AssetLocator._from_deprecated_son(id_dict, run)
