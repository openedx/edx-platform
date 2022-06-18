"""
TestCases that use property-based testing to validate properties that all
installed keys should have.
"""

import logging

from hypothesis import strategies, given, assume, example, HealthCheck, settings
from hypothesis.strategies._internal.core import cacheable
from opaque_keys.edx.keys import CourseKey, UsageKey, DefinitionKey, BlockTypeKey, AssetKey
from opaque_keys import InvalidKeyError
from opaque_keys.tests.strategies import keys_of_type

KEY_TYPES = (CourseKey, UsageKey, DefinitionKey, BlockTypeKey, AssetKey)
KEY_CLASSES = {
    extension.plugin
    for key_type in KEY_TYPES
    for extension in key_type._drivers()  # pylint: disable=protected-access
}

LOGGER = logging.getLogger(__name__)

# composite strategies confuse pylint (because they silently provide the `draw`
# argument), so we stop it from complaining about them.
# pylint: disable=no-value-for-parameter


def insert(string, index, character):
    """
    Operation to insert a character in a string.

    Arguments:
        string: The string to insert into
        index: The index to insert the character at
        character: The character to insert
    """
    return string[:index] + character + string[index:]


def delete(string, index, character):  # pylint: disable=unused-argument
    """
    Operation to delete a character from a string.

    Arguments:
        string: The string to delete from
        index: The index to delete the character at
        character: This argument is ignored, but exists to match the signatures
            of insert and replace.
    """
    return string[:index - 1] + string[index:]


def replace(string, index, character):
    """
    Operation to replace a character in a string.

    Arguments:
        string: The string to replace in
        index: The index to replace the character at
        character: The character to insert
    """
    return string[:index - 1] + character + string[index:]


@strategies.composite
def valid_key_string(draw):
    """
    A strategy that generates valid serialized OpaqueKeys.
    """
    key_type = draw(strategies.shared(strategies.sampled_from(KEY_TYPES), key="key_type"))
    key = draw(keys_of_type(key_type))
    return str(key)


@strategies.composite
def perturbed_by_character(draw, string_strategy):
    """
    A strategy that constructs a string using the supplied ``string_strategy``,
    and then perturbs it by a single character.
    """
    serialized = draw(string_strategy)
    operation = draw(strategies.sampled_from((insert, replace, delete)))
    index = draw(strategies.floats(min_value=0, max_value=1))
    character = draw(strategies.characters())
    return operation(serialized, int(len(serialized) * index), character)


@strategies.composite
def perturbed_by_subsection(draw, string_strategy):
    """
    A strategy that constructs a string using the supplied ``string_strategy``,
    and then perturbs it by replacing sections of it with other (possibly empty)
    strings.
    """
    output_string = draw(string_strategy)
    iterations = draw(strategies.integers(min_value=1, max_value=10))

    for _ in range(iterations):
        range_start = draw(strategies.integers(
            min_value=0,
            max_value=len(output_string)
        ))
        range_end = draw(strategies.integers(
            min_value=range_start,
            max_value=len(output_string)
        ))
        if range_start == range_end:
            min_size = 1
        else:
            min_size = 0
        substitution = draw(strategies.text(min_size=min_size))

        output_string = output_string[:range_start] + substitution + output_string[range_end:]

    return output_string


@cacheable
def perturbed_strings(string_strategy):
    """
    A strategy that constructs a string using the supplied ``string_strategy``,
    and then perturbs it.
    """
    return perturbed_by_character(string_strategy) | perturbed_by_subsection(string_strategy)


@given(
    key_type=strategies.shared(strategies.sampled_from(KEY_TYPES), key="key_type"),
    serialized=strategies.shared(valid_key_string(), key="diff_serial_diff_key"),
    perturbed=perturbed_strings(strategies.shared(valid_key_string(), key="diff_serial_diff_key")),
)
@settings(suppress_health_check=[HealthCheck.too_slow])
@example(
    key_type=DefinitionKey,
    serialized='def-v1:000000000000000000000000+type@-',
    perturbed='def-v1:00000000000000000000000+type@-',
)
@example(
    key_type=CourseKey,
    serialized='library-v1:-+-+branch@-+version@000000000000000000000000',
    perturbed='library-v1:-+-+branch@-+versIon@000000000000000000000000',
)
@example(
    key_type=DefinitionKey,
    serialized='aside-def-v1:def-v1:000000000000000000000000+type@-::00',
    perturbed='aside-def-v1:def-v1:000000000000000000000000+type@-\n::00',
)
@example(key_type=UsageKey, serialized='i4x://-/-/0/-', perturbed='0i4x://-/-/0/-')
@example(
    key_type=AssetKey,
    serialized='/c4x/-/-/-/-',
    perturbed='c4x/-/-/-/-',
)
@example(
    key_type=UsageKey,
    serialized='i4x://-/-/-/-@-',
    perturbed='i4x:/-/-/-/-@-',
)
@example(
    key_type=AssetKey,
    serialized='/c4x/-/-/-/-@0',
    perturbed='/c4x/-/-/-/-@0/c4x/-/-/-/-@0',
)
@example(
    key_type=UsageKey,
    serialized='lib-block-v1:-+-+branch@--+version@000000000000000000000000+type@-+block@-',
    perturbed='lib-block-v1:-+-+block@-',
)
@example(
    key_type=UsageKey,
    serialized='i4x://-/-/-/-@-',
    perturbed='/i4x/-/-/-/-@-',
)
@example(
    key_type=UsageKey,
    serialized='i4x://-/-/-/-@-',
    perturbed='i4x://-/-/-/-@-/',
)
def test_perturbed_serializations(key_type, serialized, perturbed):
    assume(serialized != perturbed)

    original_key = key_type.from_string(serialized)

    try:
        perturbed_key = key_type.from_string(perturbed)
    except InvalidKeyError:
        # The perturbed serialization didn't parse. That's ok.
        pass
    else:
        assert original_key != perturbed_key


@given(
    key_type=strategies.shared(strategies.sampled_from(KEY_TYPES), key="key_type"),
    serialized=valid_key_string(),
    perturbed=valid_key_string(),
)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_unique_deserialization(key_type, serialized, perturbed):
    assume(serialized != perturbed)

    original_key = key_type.from_string(serialized)
    perturbed_key = key_type.from_string(perturbed)
    assert original_key != perturbed_key
