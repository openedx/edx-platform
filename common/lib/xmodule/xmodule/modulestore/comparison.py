import logging

from functools import partial
from nose.tools import assert_equals
from operator import attrgetter
from types import GeneratorType

from . import ModuleStoreBase

log = logging.getLogger(__name__)

def make_compare(method_name, compare_value=lambda x: x):
    def _compare(self, *args, **kwargs):
        reference_exception = None
        reference_result = None
        try:
            reference_result = getattr(self.reference, method_name)(*args, **kwargs)

            if isinstance(reference_result, GeneratorType):
                reference_result = list(reference_result)
        except Exception as reference_exception:
            pass

        for check in self.checks:
            try:
                check_result = getattr(check, method_name)(*args, **kwargs)
                if isinstance(check_result, GeneratorType):
                    check_result = list(reference_result)
                try:
                    assert_equals(compare_value(reference_result), compare_value(check_result))
                except AssertionError as assert_error:
                    log.warning('%s: Reference and check %r differed: %s' %
                        (method_name, check, assert_error))
            except Exception as check_exception:
                if reference_exception.__class__ != check_exception.__class__:
                    log.warning('%s: Reference and check %r exceptions differed: %r != %r' %
                        (method_name, check, reference_exception, check_exception), exc_info=True)

        if reference_exception is not None:
            raise reference_exception
        return reference_result
    return _compare

def sort_by_locations(items):
    return sorted(items, key=attrgetter('location'))

class ComparisonModuleStore(ModuleStoreBase):
    """
    This modulestore performs all operations on a reference implementation and a number
    check implementations. It returns only the results from the reference implementation,
    but logs warnings for any operations where the result of the reference differs
    from the result of the check modulestore.
    """

    def __init__(self, reference, *checks):
        super(ComparisonModuleStore, self).__init__()
        self.reference = reference
        self.checks = checks

    has_item = make_compare('has_item')
    get_item = make_compare('get_item')
    get_instance = make_compare('get_instance')
    get_item_errors = make_compare('get_item_errors')
    get_items = make_compare('get_items', compare_value=sort_by_locations)
    clone_item = make_compare('clone_item')
    update_item = make_compare('update_item')
    update_children = make_compare('update_children')
    update_metadata = make_compare('update_metadata')
    delete_item = make_compare('delete_item')
    get_courses = make_compare('get_courses', compare_value=sort_by_locations)
    get_course = make_compare('get_course')
    get_parent_locations = make_compare('get_parent_locations', compare_value=lambda locs: sorted(locs))
    get_errored_courses = make_compare('get_errored_courses', compare_value=sort_by_locations)
