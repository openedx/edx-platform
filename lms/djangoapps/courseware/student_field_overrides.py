"""
API related to providing field overrides for individual students.  This is used
by the individual due dates feature.
"""


import json

from lms.djangoapps.courseware.models import StudentFieldOverride
from openedx.core.lib.xblock_utils import is_xblock_aside

from .field_overrides import FieldOverrideProvider


class IndividualStudentOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which allows for
    overrides to be made on a per user basis.
    """
    def get(self, block, name, default):
        return get_override_for_user(self.user, block, name, default)

    @classmethod
    def enabled_for(cls, course):  # pylint: disable=arguments-differ
        """This simple override provider is always enabled"""
        return True


def get_override_for_user(user, block, name, default=None):
    """
    Gets the value of the overridden field for the `user`.  `block` and `name`
    specify the block and the name of the field.  If the field is not
    overridden for the given user, returns `default`.
    """
    if not hasattr(block, '_student_overrides'):
        block._student_overrides = {}  # pylint: disable=protected-access
    overrides = block._student_overrides.get(user.id)  # pylint: disable=protected-access
    if overrides is None:
        overrides = _get_overrides_for_user(user, block)
        block._student_overrides[user.id] = overrides  # pylint: disable=protected-access
    return overrides.get(name, default)


def _get_overrides_for_user(user, block):
    """
    Gets all of the individual student overrides for given user and block.
    Returns a dictionary of field override values keyed by field name.
    """
    if (
        hasattr(block, "scope_ids") and
        hasattr(block.scope_ids, "usage_id") and
        is_xblock_aside(block.scope_ids.usage_id)
    ):
        location = block.scope_ids.usage_id.usage_key
    else:
        location = block.location

    query = StudentFieldOverride.objects.filter(
        course_id=block.scope_ids.usage_id.context_key,
        location=location,
        student_id=user.id,
    )
    overrides = {}
    for override in query:
        field = block.fields[override.field]
        value = field.from_json(json.loads(override.value))
        overrides[override.field] = value
    return overrides


def override_field_for_user(user, block, name, value):
    """
    Overrides a field for the `user`.  `block` and `name` specify the block
    and the name of the field on that block to override.  `value` is the
    value to set for the given field.
    """
    override, _ = StudentFieldOverride.objects.get_or_create(
        course_id=block.scope_ids.usage_id.context_key,
        location=block.location,
        student_id=user.id,
        field=name)
    field = block.fields[name]
    override.value = json.dumps(field.to_json(value))
    override.save()


def clear_override_for_user(user, block, name):
    """
    Clears a previously set field override for the `user`.  `block` and `name`
    specify the block and the name of the field on that block to clear.
    This function is idempotent--if no override is set, nothing action is
    performed.
    """
    try:
        StudentFieldOverride.objects.get(
            course_id=block.scope_ids.usage_id.context_key,
            student_id=user.id,
            location=block.location,
            field=name).delete()
    except StudentFieldOverride.DoesNotExist:
        pass
