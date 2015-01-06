"""
API related to providing field overrides for individual students.  This is used
by the individual due dates feature.
"""
import json
import threading

from contextlib import contextmanager

from courseware.field_overrides import FieldOverrideProvider
from pocs import ACTIVE_POC_KEY

from .models import PocMembership, PocFieldOverride


class PersonalOnlineCoursesOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which allows for
    overrides to be made on a per user basis.
    """
    def get(self, block, name, default):
        poc = get_current_poc(self.user)
        if poc:
            return get_override_for_poc(poc, block, name, default)
        return default


class _PocContext(threading.local):
    """
    A threading local used to implement the `with_poc` context manager, that
    keeps track of the POC currently set as the context.
    """
    poc = None


_POC_CONTEXT = _PocContext()


@contextmanager
def poc_context(poc):
    """
    A context manager which can be used to explicitly set the POC that is in
    play for field overrides.  This mechanism overrides the standard mechanism
    of looking in the user's session to see if they are enrolled in a POC and
    viewing that POC.
    """
    prev = _POC_CONTEXT.poc
    _POC_CONTEXT.poc = poc
    yield
    _POC_CONTEXT.poc = prev


def get_current_poc(user):
    """
    Return the poc that is active for this request.
    """
    poc = _POC_CONTEXT.poc
    if poc:
        return poc


def get_override_for_poc(poc, block, name, default=None):
    """
    Gets the value of the overridden field for the `poc`.  `block` and `name`
    specify the block and the name of the field.  If the field is not
    overridden for the given poc, returns `default`.
    """
    if not hasattr(block, '_poc_overrides'):
        block._poc_overrides = {}
    overrides = block._poc_overrides.get(poc.id)
    if overrides is None:
        overrides = _get_overrides_for_poc(poc, block)
        block._poc_overrides[poc.id] = overrides
    return overrides.get(name, default)


def _get_overrides_for_poc(poc, block):
    """
    Returns a dictionary mapping field name to overriden value for any
    overrides set on this block for this POC.
    """
    overrides = {}
    query = PocFieldOverride.objects.filter(
        poc=poc,
        location=block.location
    )
    for override in query:
        field = block.fields[override.field]
        value = field.from_json(json.loads(override.value))
        overrides[override.field] = value
    return overrides


def override_field_for_poc(poc, block, name, value):
    """
    Overrides a field for the `poc`.  `block` and `name` specify the block
    and the name of the field on that block to override.  `value` is the
    value to set for the given field.
    """
    override, created = PocFieldOverride.objects.get_or_create(
        poc=poc,
        location=block.location,
        field=name)
    field = block.fields[name]
    override.value = json.dumps(field.to_json(value))
    override.save()

    if hasattr(block, '_poc_overrides'):
        del block._poc_overrides[poc.id]


def clear_override_for_poc(poc, block, name):
    """
    Clears a previously set field override for the `poc`.  `block` and `name`
    specify the block and the name of the field on that block to clear.
    This function is idempotent--if no override is set, nothing action is
    performed.
    """
    try:
        PocFieldOverride.objects.get(
            poc=poc,
            location=block.location,
            field=name).delete()

        if hasattr(block, '_poc_overrides'):
            del block._poc_overrides[poc.id]

    except PocFieldOverride.DoesNotExist:
        pass


class PocMiddleware(object):
    """
    Checks to see if current session is examining a POC and sets the POC as
    the current POC for the override machinery if so.
    """
    def process_request(self, request):
        """
        Do the check.
        """
        poc_id = request.session.get(ACTIVE_POC_KEY, None)
        if poc_id is not None:
            try:
                membership = PocMembership.objects.get(
                    student=request.user, active=True, poc__id__exact=poc_id
                )
                _POC_CONTEXT.poc = membership.poc
            except PocMembership.DoesNotExist:
                # if there is no membership, be sure to unset the active poc
                _POC_CONTEXT.poc = None
                request.session.pop(ACTIVE_POC_KEY)

    def process_response(self, request, response):
        """
        Clean up afterwards.
        """
        _POC_CONTEXT.poc = None
        return response
