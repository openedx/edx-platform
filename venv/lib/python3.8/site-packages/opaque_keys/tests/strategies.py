"""
``hypothesis`` strategies for generating OpaqueKey objects.
"""

from functools import singledispatch, update_wrapper
import string

from hypothesis import strategies, assume
from hypothesis.strategies._internal.core import cacheable

from opaque_keys.edx.block_types import BlockTypeKeyV1, XBLOCK_V1, XMODULE_V1
from opaque_keys.edx.asides import (
    AsideDefinitionKeyV2, AsideUsageKeyV2, AsideDefinitionKeyV1, AsideUsageKeyV1
)
from opaque_keys.edx.keys import (
    AsideDefinitionKey,
    AsideUsageKey,
    DefinitionKey,
    UsageKey,
)
from opaque_keys.edx.locations import DeprecatedLocation
from opaque_keys.edx.locator import (
    BlockUsageLocator,
    BundleDefinitionLocator,
    CourseLocator,
    DefinitionLocator,
    LibraryLocator,
    LibraryLocatorV2,
    LibraryUsageLocator,
    LibraryUsageLocatorV2,
)


@cacheable
def unicode_letters_and_digits():
    """
    Strategy to return unicode characters and numbers.
    """
    return strategies.characters(
        whitelist_categories=[
            'Lu',  # Uppercase letters
            'Ll',  # Lowercase letters
            'Lt',  # Titlecase letters
            'Lm',  # Modifier letters
            'Lo',  # Other letters
            'Nd',  # Decimal digit numbers
            'No',  # Other number
        ]
    )


@cacheable
def ascii_identifier():
    """
    Strategy to generate a slug with no unicode
    """
    return strategies.text(
        alphabet=strategies.sampled_from("-._abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        min_size=1,
        max_size=20,
    )


@cacheable
def allowed_locator_ids():
    """
    Strategy to generate valid ids for Locator fields.
    """
    return strategies.text(
        alphabet=unicode_letters_and_digits() | strategies.sampled_from("-~.:"),
        min_size=1,
    )


@cacheable
def deprecated_locator_ids():
    """
    Strategy to generate valid ids for deprecated Locator fields.
    """
    return strategies.text(
        alphabet=unicode_letters_and_digits() | strategies.sampled_from("-~.:%"),
        min_size=1,
    )


@cacheable
def deprecated_course_ids():
    """
    Strategy to generate valid ids for deprecated CourseLocator fields.
    """
    return strategies.text(
        alphabet=unicode_letters_and_digits() | strategies.sampled_from("-.%"),
        min_size=1,
    )


@cacheable
def version_guids():
    """
    Strategy to generate valid ObjectIds.
    """
    return strategies.text(alphabet=string.hexdigits, min_size=24, max_size=24)


def classdispatch(func):
    """
    Like ``singledispatch``, this allows you to write a generic function that
    with implementations that differ on type. However, unlike ``singledispatch``,
    this expects a class as the first argument, and dispatches on that class,
    rather than expecting an instance of a class, and dispatching on the class
    of the instance.
    """
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):  # pylint: disable=missing-docstring
        return dispatcher.dispatch(args[0])(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper


@classdispatch
@cacheable
def fields_for_key(cls, field):  # pylint: disable=unused-argument
    """
    A ``hypothesis`` strategy to generate data of the right type for the fields of this OpaqueKey.

    Arguments:
        field: The name of the field to generate data for.
    """
    if field == 'deprecated':
        return strategies.booleans()
    return strategies.text(min_size=1)


@strategies.composite
def _aside_v1_exclusions(draw, strategy):
    """
    A strategy that can be wrapped around another to exclude
    strings not allowed by _join_keys_v1, and thus not allowed by
    AsideDefinitionKeyV1 or AsideUsageKeyV1.
    """
    key = draw(strategy)
    serialized = str(key)
    assume('::' not in serialized)
    assume(not serialized.endswith(':'))
    return key


@fields_for_key.register(AsideDefinitionKeyV1)
@cacheable
def _fields_for_aside_def_key_v1(cls, field):  # pylint: disable=missing-docstring
    if field == 'deprecated':
        return strategies.just(False)
    if field == 'definition_key':
        return _aside_v1_exclusions(  # pylint: disable=no-value-for-parameter
            keys_of_type(DefinitionKey, blacklist=AsideDefinitionKey)
        )
    return fields_for_key(super(AsideDefinitionKeyV1, cls).__class__, field)


@fields_for_key.register(AsideUsageKeyV1)
@cacheable
def _fields_for_aside_usage_key_v1(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'deprecated':
        return strategies.just(False)
    if field == 'usage_key':
        return _aside_v1_exclusions(  # pylint: disable=no-value-for-parameter
            keys_of_type(UsageKey, blacklist=AsideUsageKey)
        )
    return fields_for_key(super(AsideUsageKeyV1, cls).__class__, field)


@fields_for_key.register(AsideDefinitionKeyV2)
@cacheable
def _fields_for_aside_def_key_v2(cls, field):  # pylint: disable=missing-docstring
    if field == 'deprecated':
        return strategies.just(False)
    if field == 'definition_key':
        return keys_of_type(DefinitionKey, blacklist=AsideDefinitionKey)
    return fields_for_key(super(AsideDefinitionKeyV2, cls).__class__, field)


@fields_for_key.register(AsideUsageKeyV2)
@cacheable
def _fields_for_aside_usage_key_v2(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'deprecated':
        return strategies.just(False)
    if field == 'usage_key':
        return keys_of_type(UsageKey, blacklist=AsideUsageKey)
    return fields_for_key(super(AsideUsageKeyV2, cls).__class__, field)


@fields_for_key.register(LibraryLocator)
@cacheable
def _fields_for_library_locator(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'version_guid':
        return version_guids()
    if field in ('org', 'library', 'branch'):
        return allowed_locator_ids()
    if field == 'deprecated':
        return strategies.just(False)
    return fields_for_key(super(LibraryLocator, cls).__class__, field)


@fields_for_key.register(LibraryLocatorV2)
@cacheable
def _fields_for_library_locator_v2(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'org':
        return ascii_identifier()
    if field == 'slug':
        return strategies.text(alphabet=unicode_letters_and_digits(), min_size=1)
    return fields_for_key(super(LibraryLocatorV2, cls).__class__, field)


@fields_for_key.register(DefinitionLocator)
@cacheable
def _fields_for_definition_locator(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'definition_id':
        return version_guids()
    if field == 'block_type':
        return allowed_locator_ids()
    return fields_for_key(super(DefinitionLocator, cls).__class__, field)


@fields_for_key.register(BundleDefinitionLocator)
@cacheable
def _fields_for_bundle_def_locator(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'bundle_uuid':
        return strategies.uuids()
    if field == 'block_type':
        return ascii_identifier()
    if field == 'olx_path':
        return strategies.just("some/path/to/definition.xml")
    if field == '_version_or_draft':
        return strategies.sampled_from((1, 2, 3, "studio_draft", "draft1", "d1", "1d"))
    return fields_for_key(super(DefinitionLocator, cls).__class__, field)


@fields_for_key.register(LibraryUsageLocatorV2)
@cacheable
def _fields_for_library_locator_v2(cls, field):  # pylint: disable=missing-docstring, function-redefined
    if field == 'lib_key':
        return instances_of_key(LibraryLocatorV2)
    if field == 'block_type':
        return ascii_identifier()
    if field == 'usage_id':
        return strategies.text(alphabet=unicode_letters_and_digits(), min_size=1)
    return fields_for_key(super(LibraryUsageLocatorV2, cls).__class__, field)


@classdispatch
@cacheable
def instances_of_key(cls, **kwargs):
    """
    A ``hypothesis`` strategy to generate instances of this OpaqueKey class.

    Arguments:
        **kwargs: Use this to override the strategy used for any of the
            KEY_FIELDS when building this class.
    """
    field_names = cls.KEY_FIELDS
    # add deprecated=False for classes that accept that argument:
    no_deprecated_field = (BundleDefinitionLocator, LibraryLocatorV2, LibraryUsageLocatorV2)
    if cls not in no_deprecated_field:
        field_names = field_names + ('deprecated', )
    key_fields = {
        field: kwargs.get(field, fields_for_key(cls, field))
        for field in field_names
    }
    return strategies.builds(
        cls,
        **key_fields
    )


@instances_of_key.register(BlockTypeKeyV1)
@cacheable
def _instances_of_block_type_key(cls, **kwargs):  # pylint: disable=missing-docstring, function-redefined

    return strategies.builds(
        cls,
        block_family=kwargs.get('block_family', (
            strategies.text(
                alphabet=strategies.characters(blacklist_characters=':'),
                min_size=1,
            ) | strategies.sampled_from((XBLOCK_V1, XMODULE_V1))
        )),
        block_type=kwargs.get('block_type', strategies.text(min_size=1)),
    )


@instances_of_key.register(CourseLocator)
@cacheable
def _instances_of_course_locator(cls, **kwargs):  # pylint: disable=missing-docstring, function-redefined

    return strategies.builds(
        cls,
        org=kwargs.get('org', deprecated_course_ids()),
        course=kwargs.get('course', deprecated_course_ids()),
        run=kwargs.get('run', deprecated_course_ids()),
        branch=kwargs.get('branch', deprecated_course_ids() | strategies.none()),
        deprecated=strategies.just(True),
    ) | strategies.builds(
        cls,
        org=kwargs.get('org', allowed_locator_ids()),
        course=kwargs.get('course', allowed_locator_ids()),
        run=kwargs.get('run', allowed_locator_ids()),
        branch=kwargs.get('branch', allowed_locator_ids()),
        version_guid=kwargs.get('version_guid', version_guids()),
        deprecated=strategies.just(False),
    )


@instances_of_key.register(BlockUsageLocator)
@cacheable
def _instances_of_block_usage(cls, **kwargs):  # pylint: disable=missing-docstring, function-redefined

    def locator_for_course(course_key):
        """
        Strategy that, given a ``course_locator``, will construct a BlockUsageLocator
        in that course.
        """
        if course_key.deprecated:
            return strategies.builds(
                cls,
                course_key=strategies.just(course_key),
                block_id=kwargs.get('block_id', deprecated_course_ids()),
                block_type=kwargs.get('block_type', deprecated_course_ids()),
                deprecated=kwargs.get('deprecated', strategies.booleans()),
            )
        return strategies.builds(
            cls,
            course_key=strategies.just(course_key),
            block_id=kwargs.get('block_id', allowed_locator_ids()),
            block_type=kwargs.get('block_type', allowed_locator_ids()),
            deprecated=kwargs.get('deprecated', strategies.booleans()),
        )

    return kwargs.get('course_key', instances_of_key(CourseLocator)).flatmap(locator_for_course)


@instances_of_key.register(LibraryUsageLocator)
@cacheable
def _instances_of_library_usage(cls, **kwargs):  # pylint: disable=missing-docstring, function-redefined

    return strategies.builds(
        cls,
        library_key=kwargs.get('library_key', instances_of_key(LibraryLocator)),
        block_id=kwargs.get('block_id', allowed_locator_ids()),
        block_type=kwargs.get('block_type', allowed_locator_ids()),
    )


@instances_of_key.register(DeprecatedLocation)
@cacheable
def _instances_of_deprecated_loc(cls, **kwargs):  # pylint: disable=missing-docstring, function-redefined

    return strategies.builds(
        cls,
        course_key=kwargs.get('course_key', instances_of_key(
            CourseLocator,
            version_guid=strategies.none(),
            branch=strategies.none(),
        )),
        block_id=kwargs.get('block_id', allowed_locator_ids()),
        block_type=kwargs.get('block_type', allowed_locator_ids()),
    )


@classdispatch
@cacheable
def keys_of_type(cls, blacklist=None):
    """
    A ``hypothesis`` strategy to generate instances of this OpaqueKey KeyType.

    This is only used for property-based testing.
    """
    if blacklist is None:
        blacklist = ()
    return strategies.one_of(*[
        instances_of_key(extension.plugin)
        for extension in cls._drivers()  # pylint: disable=protected-access
        if not(issubclass(extension.plugin, blacklist))
    ])
