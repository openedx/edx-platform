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
from ccx_keys.locator import CCXLocator, CCXBlockUsageLocator
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator


def ccx_locator_to_course_locator(ccx_locator):
    return CourseLocator(
        org=ccx_locator.org,
        course=ccx_locator.course,
        run=ccx_locator.run,
        branch=ccx_locator.branch,
        version_guid=ccx_locator.version_guid,
    )


def strip_ccx(val):
    retval = val
    ccx_id = None
    if hasattr(retval, 'ccx'):
        if isinstance(retval, CCXLocator):
            ccx_id = retval.ccx
            retval = ccx_locator_to_course_locator(retval)
        elif isinstance(object, CCXBlockUsageLocator):
            ccx_locator = retval.course_key
            ccx_id = ccx_locator.ccx
            course_locator = ccx_locator_to_course_locator(ccx_locator)
            retval = BlockUsageLocator(
                course_locator, retval.block_type, retval.block_id
            )
    if hasattr(retval, 'location'):
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


def restore_ccx_collection(field_value, ccx_id):
    if isinstance(field_value, list):
        field_value = [restore_ccx(fv, ccx_id) for fv in field_value]
    elif isinstance(field_value, dict):
        for key, val in field_value.iteritems():
            field_value[key] = restore_ccx(val, ccx_id)
    else:
        field_value = restore_ccx(field_value, ccx_id)
    return field_value


class CCXModulestoreWrapper(object):

    def __init__(self, modulestore):
        self._modulestore = modulestore

    def __getattr__(self, name):
        """pass missing attributes through to _modulestore
        """
        return getattr(self._modulestore, name)

    def _clean_locator_for_mapping(self, locator):
        locator, ccx = strip_ccx(locator)
        retval = self._modulestore._clean_locator_for_mapping(locator)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def _get_modulestore_for_courselike(self, locator=None):
        if locator is not None:
            locator, _ = strip_ccx(locator)
        return self._modulestore._get_modulestore_for_courselike(locator)

    def fill_in_run(self, course_key):
        """
        Some course_keys are used without runs. This function calls the corresponding
        fill_in_run function on the appropriate modulestore.
        """
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.fill_in_run(course_key)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

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
        usage_key, ccx = strip_ccx(usage_key)
        retval = self._modulestore.get_item(usage_key, depth, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def get_items(self, course_key, **kwargs):
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.get_items(course_key, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def get_course(self, course_key, depth=0, **kwargs):
        # from nose.tools import set_trace; set_trace()
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.get_course(course_key, depth=depth, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def has_course(self, course_id, ignore_case=False, **kwargs):
        course_id, ccx = strip_ccx(course_id)
        retval = self._modulestore.has_course(
            course_id, ignore_case=ignore_case, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def delete_course(self, course_key, user_id):
        """
        See xmodule.modulestore.__init__.ModuleStoreWrite.delete_course
        """
        course_key, ccx = strip_ccx(course_key)
        return self._modulestore.delete_course(course_key, user_id)

    def get_parent_location(self, location, **kwargs):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.get_parent_location(location, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def get_block_original_usage(self, usage_key):
        usage_key, ccx = strip_ccx(usage_key)
        orig_key, version = self._modulestore.get_block_original_usage(usage_key)
        if orig_key and ccx:
            orig_key = restore_ccx_collection(orig_key, ccx)
        return orig_key, version

    def get_modulestore_type(self, course_id):
        course_id, ccx = strip_ccx(course_id)
        retval = self._modulestore.get_modulestore_type(course_id)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def get_orphans(self, course_key, **kwargs):
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.get_orphans(course_key, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

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
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.create_item(
            user_id, course_key, block_type, block_id=block_id, fields=fields, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        parent_usage_key, ccx = strip_ccx(parent_usage_key)
        retval = self._modulestore.create_child(
            user_id, parent_usage_key, block_type, block_id=block_id, fields=fields, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.import_xblock(
            user_id, course_key, block_type, block_id, fields=fields, runtime=runtime, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def copy_from_template(self, source_keys, dest_key, user_id, **kwargs):
        dest_key, ccx = strip_ccx(dest_key)
        retval = self._modulestore.copy_from_template(
            source_keys, dest_key, user_id, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def update_item(self, xblock, user_id, allow_not_found=False, **kwargs):
        xblock, ccx = strip_ccx(xblock)
        retval = self._modulestore.update_item(
            xblock, user_id, allow_not_found=allow_not_found, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def delete_item(self, location, user_id, **kwargs):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.delete_item(location, user_id, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def revert_to_published(self, location, user_id):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.revert_to_published(location, user_id)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def create_xblock(self, runtime, course_key, block_type, block_id=None, fields=None, **kwargs):
        course_key, ccx = strip_ccx(course_key)
        retval = self._modulestore.create_xblock(
            runtime, course_key, block_type, block_id=block_id, fields=fields, **kwargs
        )
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def has_published_version(self, xblock):
        xblock.scope_ids.usage_id.course_key, ccx = strip_ccx(
            xblock.scope_ids.usage_id.course_key
        )
        retval = self._modulestore.has_published_version(xblock)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def publish(self, location, user_id, **kwargs):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.publish(location, user_id, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def unpublish(self, location, user_id, **kwargs):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.unpublish(location, user_id, **kwargs)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def convert_to_draft(self, location, user_id):
        location, ccx = strip_ccx(location)
        retval = self._modulestore.convert_to_draft(location, user_id)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

    def has_changes(self, xblock):
        xblock.location, ccx = strip_ccx(xblock.location)
        retval = self._modulestore.has_changes(xblock)
        if ccx:
            retval = restore_ccx_collection(retval, ccx)
        return retval

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
