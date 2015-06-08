# -*- coding: utf-8 -*-
"""A modulestore wrapper

It will 'unwrap' ccx keys on the way in and re-wrap them on the way out

In practical terms this means that when an object is retrieved from modulestore
using a CCXLocator or CCXBlockUsageLocator as the key, the equivalent
CourseLocator or BlockUsageLocator will actually be used. And all objects
returned from the modulestore will have their keys updated to be the CCX
version that was passed in.
"""
from contextlib import contextmanager
from functools import partial
from ccx_keys.locator import CCXLocator, CCXBlockUsageLocator
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator


def strip_ccx(val):
    retval = val
    ccx_id = None
    if isinstance(retval, CCXLocator):
        ccx_id = retval.ccx
        retval = retval.to_course_locator()
    elif isinstance(object, CCXBlockUsageLocator):
        ccx_id = retval.course_key.ccx
        retval = retval.to_block_locator()
    elif hasattr(retval, 'location'):
        retval.location, ccx_id = strip_ccx(retval.location)
    return retval, ccx_id


def restore_ccx(val, ccx_id):
    if isinstance(val, CourseLocator):
        return CCXLocator.from_course_locator(val, ccx_id)
    elif isinstance(val, BlockUsageLocator):
        ccx_key = restore_ccx(val.course_key, ccx_id)
        val = CCXBlockUsageLocator(ccx_key, val.block_type, val.block_id)
    if hasattr(val, 'location'):
        val.location = restore_ccx(val.location, ccx_id)
    if hasattr(val, 'children'):
        val.children = restore_ccx_collection(val.children, ccx_id)
    return val


def restore_ccx_collection(field_value, ccx_id=None):
    if ccx_id is None:
        return field_value
    if isinstance(field_value, list):
        field_value = [restore_ccx(fv, ccx_id) for fv in field_value]
    elif isinstance(field_value, dict):
        for key, val in field_value.iteritems():
            field_value[key] = restore_ccx(val, ccx_id)
    else:
        field_value = restore_ccx(field_value, ccx_id)
    return field_value


@contextmanager
def remove_ccx(to_strip):
    stripped, ccx = strip_ccx(to_strip)
    yield stripped, partial(restore_ccx_collection, ccx_id=ccx)


class CCXModulestoreWrapper(object):

    def __init__(self, modulestore):
        self._modulestore = modulestore

    def __getattr__(self, name):
        """pass missing attributes through to _modulestore
        """
        return getattr(self._modulestore, name)

    def _clean_locator_for_mapping(self, locator):
        with remove_ccx(locator) as stripped:
            locator, restore = stripped
            retval = self._modulestore._clean_locator_for_mapping(locator)
            return restore(retval)

    def _get_modulestore_for_courselike(self, locator=None):
        if locator is not None:
            locator, _ = strip_ccx(locator)
        return self._modulestore._get_modulestore_for_courselike(locator)

    def fill_in_run(self, course_key):
        """
        Some course_keys are used without runs. This function calls the corresponding
        fill_in_run function on the appropriate modulestore.
        """
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.fill_in_run(course_key)
            return restore(retval)

    def has_item(self, usage_key, **kwargs):
        """
        Does the course include the xblock who's id is reference?
        """
        usage_key, ccx = strip_ccx(usage_key)
        return self._modulestore.has_item(usage_key, **kwargs)

    def get_item(self, usage_key, depth=0, **kwargs):
        """
        see parent doc
        """
        with remove_ccx(usage_key) as stripped:
            usage_key, restore = stripped
            retval = self._modulestore.get_item(usage_key, depth, **kwargs)
            return restore(retval)

    def get_items(self, course_key, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.get_items(course_key, **kwargs)
            return restore(retval)

    def get_course(self, course_key, depth=0, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.get_course(
                course_key, depth=depth, **kwargs
            )
            return restore(retval)

    def has_course(self, course_id, ignore_case=False, **kwargs):
        with remove_ccx(course_id) as stripped:
            course_id, restore = stripped
            retval = self._modulestore.has_course(
                course_id, ignore_case=ignore_case, **kwargs
            )
            return restore(retval)

    def delete_course(self, course_key, user_id):
        """
        See xmodule.modulestore.__init__.ModuleStoreWrite.delete_course
        """
        course_key, ccx = strip_ccx(course_key)
        return self._modulestore.delete_course(course_key, user_id)

    def get_parent_location(self, location, **kwargs):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.get_parent_location(location, **kwargs)
            return restore(retval)

    def get_block_original_usage(self, usage_key):
        with remove_ccx(usage_key) as stripped:
            usage_key, restore = stripped
            orig_key, version = self._modulestore.get_block_original_usage(usage_key)
            return restore(orig_key), version

    def get_modulestore_type(self, course_id):
        with remove_ccx(course_id) as stripped:
            course_id, restore = stripped
            retval = self._modulestore.get_modulestore_type(course_id)
            return restore(retval)

    def get_orphans(self, course_key, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.get_orphans(course_key, **kwargs)
            return restore(retval)

    def clone_course(self, source_course_id, dest_course_id, user_id, fields=None, **kwargs):
        source_course_id, source_ccx = strip_ccx(source_course_id)
        dest_course_id, dest_ccx = strip_ccx(dest_course_id)
        retval = self._modulestore.clone_course(
            source_course_id, dest_course_id, user_id, fields=fields, **kwargs
        )
        if dest_ccx:
            retval = restore_ccx_collection(retval, dest_ccx)
        return retval

    def create_item(self, user_id, course_key, block_type, block_id=None, fields=None, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.create_item(
                user_id, course_key, block_type, block_id=block_id, fields=fields, **kwargs
            )
            return restore(retval)

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        with remove_ccx(parent_usage_key) as stripped:
            parent_usage_key, restore = stripped
            retval = self._modulestore.create_child(
                user_id, parent_usage_key, block_type, block_id=block_id, fields=fields, **kwargs
            )
            return restore(retval)

    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.import_xblock(
                user_id, course_key, block_type, block_id, fields=fields, runtime=runtime, **kwargs
            )
            return restore(retval)

    def copy_from_template(self, source_keys, dest_key, user_id, **kwargs):
        with remove_ccx(dest_key) as stripped:
            dest_key, restore = stripped
            retval = self._modulestore.copy_from_template(
                source_keys, dest_key, user_id, **kwargs
            )
            return restore(retval)

    def update_item(self, xblock, user_id, allow_not_found=False, **kwargs):
        with remove_ccx(xblock) as stripped:
            xblock, restore = stripped
            retval = self._modulestore.update_item(
                xblock, user_id, allow_not_found=allow_not_found, **kwargs
            )
            return restore(retval)

    def delete_item(self, location, user_id, **kwargs):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.delete_item(location, user_id, **kwargs)
            return restore(retval)

    def revert_to_published(self, location, user_id):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.revert_to_published(location, user_id)
            return restore(retval)

    def create_xblock(self, runtime, course_key, block_type, block_id=None, fields=None, **kwargs):
        with remove_ccx(course_key) as stripped:
            course_key, restore = stripped
            retval = self._modulestore.create_xblock(
                runtime, course_key, block_type, block_id=block_id, fields=fields, **kwargs
            )
            return restore(retval)

    def has_published_version(self, xblock):
        with remove_ccx(xblock) as stripped:
            xblock, restore = stripped
            retval = self._modulestore.has_published_version(xblock)
            return restore(retval)

    def publish(self, location, user_id, **kwargs):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.publish(location, user_id, **kwargs)
            return restore(retval)

    def unpublish(self, location, user_id, **kwargs):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.unpublish(location, user_id, **kwargs)
            return restore(retval)

    def convert_to_draft(self, location, user_id):
        with remove_ccx(location) as stripped:
            location, restore = stripped
            retval = self._modulestore.convert_to_draft(location, user_id)
            return restore(retval)

    def has_changes(self, xblock):
        with remove_ccx(xblock) as stripped:
            xblock, restore = stripped
            retval = self._modulestore.has_changes(xblock)
            return restore(retval)

    def check_supports(self, course_key, method):
        course_key, _ = strip_ccx(course_key)
        return self._modulestore.check_supports(course_key, method)

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):
        """
        A context manager for temporarily setting the branch value for the given course' store
        to the given branch_setting.  If course_id is None, the default store is used.
        """
        course_id, _ = strip_ccx(course_id)
        with self._modulestore.branch_setting(branch_setting, course_id):
            yield

    @contextmanager
    def bulk_operations(self, course_id, emit_signals=True):
        course_id, _ = strip_ccx(course_id)
        with self._modulestore.bulk_operations(course_id, emit_signals=emit_signals):
            yield
