"""
API related to providing field overrides for individual students.  This is used
by the individual custom courses feature.
"""
import json
import threading

from contextlib import contextmanager

from django.db import transaction, IntegrityError

from courseware.field_overrides import FieldOverrideProvider  # pylint: disable=import-error
from ccx import ACTIVE_CCX_KEY  # pylint: disable=import-error

from .models import CcxMembership, CcxFieldOverride


class CustomCoursesForEdxOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which allows for
    overrides to be made on a per user basis.
    """
    def get(self, block, name, default):
        """
        Just call the get_override_for_ccx method if there is a ccx
        """
        ccx = get_current_ccx()
        if ccx:
            return get_override_for_ccx(ccx, block, name, default)
        return default


class _CcxContext(threading.local):
    """
    A threading local used to implement the `with_ccx` context manager, that
    keeps track of the CCX currently set as the context.
    """
    ccx = None
    request = None


_CCX_CONTEXT = _CcxContext()


@contextmanager
def ccx_context(ccx):
    """
    A context manager which can be used to explicitly set the CCX that is in
    play for field overrides.  This mechanism overrides the standard mechanism
    of looking in the user's session to see if they are enrolled in a CCX and
    viewing that CCX.
    """
    prev = _CCX_CONTEXT.ccx
    _CCX_CONTEXT.ccx = ccx
    yield
    _CCX_CONTEXT.ccx = prev


def get_current_ccx():
    """
    Return the ccx that is active for this request.
    """
    return _CCX_CONTEXT.ccx


def get_current_request():
    """
    Return the active request, so that we can get context information in places
    where it is limited, like in the tabs.
    """
    request = _CCX_CONTEXT.request
    return request


def get_override_for_ccx(ccx, block, name, default=None):
    """
    Gets the value of the overridden field for the `ccx`.  `block` and `name`
    specify the block and the name of the field.  If the field is not
    overridden for the given ccx, returns `default`.
    """
    if not hasattr(block, '_ccx_overrides'):
        block._ccx_overrides = {}  # pylint: disable=protected-access
    overrides = block._ccx_overrides.get(ccx.id)  # pylint: disable=protected-access
    if overrides is None:
        overrides = _get_overrides_for_ccx(ccx, block)
        block._ccx_overrides[ccx.id] = overrides  # pylint: disable=protected-access
    return overrides.get(name, default)


def _get_overrides_for_ccx(ccx, block):
    """
    Returns a dictionary mapping field name to overriden value for any
    overrides set on this block for this CCX.
    """
    overrides = {}
    query = CcxFieldOverride.objects.filter(
        ccx=ccx,
        location=block.location
    )
    for override in query:
        field = block.fields[override.field]
        value = field.from_json(json.loads(override.value))
        overrides[override.field] = value
    return overrides


@transaction.commit_on_success
def override_field_for_ccx(ccx, block, name, value):
    """
    Overrides a field for the `ccx`.  `block` and `name` specify the block
    and the name of the field on that block to override.  `value` is the
    value to set for the given field.
    """
    field = block.fields[name]
    value = json.dumps(field.to_json(value))
    try:
        override = CcxFieldOverride.objects.create(
            ccx=ccx,
            location=block.location,
            field=name,
            value=value)
    except IntegrityError:
        transaction.commit()
        override = CcxFieldOverride.objects.get(
            ccx=ccx,
            location=block.location,
            field=name)
        override.value = value
    override.save()
    if hasattr(block, '_ccx_overrides'):
        del block._ccx_overrides[ccx.id]  # pylint: disable=protected-access


def clear_override_for_ccx(ccx, block, name):
    """
    Clears a previously set field override for the `ccx`.  `block` and `name`
    specify the block and the name of the field on that block to clear.
    This function is idempotent--if no override is set, nothing action is
    performed.
    """
    try:
        CcxFieldOverride.objects.get(
            ccx=ccx,
            location=block.location,
            field=name).delete()

        if hasattr(block, '_ccx_overrides'):
            del block._ccx_overrides[ccx.id]  # pylint: disable=protected-access

    except CcxFieldOverride.DoesNotExist:
        pass


class CcxMiddleware(object):
    """
    Checks to see if current session is examining a CCX and sets the CCX as
    the current CCX for the override machinery if so.
    """
    def process_request(self, request):
        """
        Do the check.
        """
        ccx_id = request.session.get(ACTIVE_CCX_KEY, None)
        if ccx_id is not None:
            try:
                membership = CcxMembership.objects.get(
                    student=request.user, active=True, ccx__id__exact=ccx_id
                )
                _CCX_CONTEXT.ccx = membership.ccx
            except CcxMembership.DoesNotExist:
                # if there is no membership, be sure to unset the active ccx
                _CCX_CONTEXT.ccx = None
                request.session.pop(ACTIVE_CCX_KEY)

        _CCX_CONTEXT.request = request

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """
        Clean up afterwards.
        """
        _CCX_CONTEXT.ccx = None
        _CCX_CONTEXT.request = None
        return response
