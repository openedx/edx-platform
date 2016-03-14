"""Views for items (modules)."""
from __future__ import absolute_import

import hashlib
import logging
from uuid import uuid4
from datetime import datetime
from pytz import UTC
import json

from collections import OrderedDict
from functools import partial
from static_replace import replace_static_urls
from openedx.core.lib.xblock_utils import wrap_xblock, request_token

import dogstats_wrapper as dog_stats_api
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from xblock.fields import Scope
from xblock.fragment import Fragment

import xmodule
from xmodule.tabs import CourseTabList
from xmodule.modulestore import ModuleStoreEnum, EdxJSONEncoder
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES
from xmodule.x_module import PREVIEW_VIEWS, STUDIO_VIEW, STUDENT_VIEW, DEPRECATION_VSCOMPAT_EVENT

from xmodule.course_module import DEFAULT_START_DATE
from django.contrib.auth.models import User
from util.date_utils import get_default_time_display

from util.json_request import expect_json, JsonResponse
from util.milestones_helpers import is_entrance_exams_enabled

from student.auth import has_studio_write_access, has_studio_read_access
from contentstore.utils import (
    find_release_date_source, find_staff_lock_source, is_currently_visible_to_students,
    ancestor_has_staff_lock, has_children_visible_to_specific_content_groups,
    get_user_partition_info,
)
from contentstore.views.helpers import is_unit, xblock_studio_url, xblock_primary_child_category, \
    xblock_type_display_name, get_parent_xblock, create_xblock, usage_key_with_run
from contentstore.views.preview import get_preview_fragment
from edxmako.shortcuts import render_to_string
from models.settings.course_grading import CourseGradingModel
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryUsageLocator
from cms.lib.xblock.authoring_mixin import VISIBILITY_VIEW

__all__ = [
    'orphan_handler', 'xblock_handler', 'xblock_view_handler', 'xblock_outline_handler', 'xblock_container_handler'
]

log = logging.getLogger(__name__)

CREATE_IF_NOT_FOUND = ['course_info']

# Useful constants for defining predicates
NEVER = lambda x: False
ALWAYS = lambda x: True


def hash_resource(resource):
    """
    Hash a :class:`xblock.fragment.FragmentResource`.
    """
    md5 = hashlib.md5()
    md5.update(repr(resource))
    return md5.hexdigest()


def _filter_entrance_exam_grader(graders):
    """
    If the entrance exams feature is enabled we need to hide away the grader from
    views/controls like the 'Grade as' dropdown that allows a course author to select
    the grader type for a given section of a course
    """
    if is_entrance_exams_enabled():
        graders = [grader for grader in graders if grader.get('type') != u'Entrance Exam']
    return graders


@require_http_methods(("DELETE", "GET", "PUT", "POST", "PATCH"))
@login_required
@expect_json
def xblock_handler(request, usage_key_string):
    """
    The restful handler for xblock requests.

    DELETE
        json: delete this xblock instance from the course.
    GET
        json: returns representation of the xblock (locator id, data, and metadata).
              if ?fields=graderType, it returns the graderType for the unit instead of the above.
        html: returns HTML for rendering the xblock (which includes both the "preview" view and the "editor" view)
    PUT or POST or PATCH
        json: if xblock locator is specified, update the xblock instance. The json payload can contain
              these fields, all optional:
                :data: the new value for the data.
                :children: the unicode representation of the UsageKeys of children for this xblock.
                :metadata: new values for the metadata fields. Any whose values are None will be deleted not set
                       to None! Absent ones will be left alone.
                :nullout: which metadata fields to set to None
                :graderType: change how this unit is graded
                :publish: can be:
                  'make_public': publish the content
                  'republish': publish this item *only* if it was previously published
                  'discard_changes' - reverts to the last published version
                Note: If 'discard_changes', the other fields will not be used; that is, it is not possible
                to update and discard changes in a single operation.
              The JSON representation on the updated xblock (minus children) is returned.

              if usage_key_string is not specified, create a new xblock instance, either by duplicating
              an existing xblock, or creating an entirely new one. The json playload can contain
              these fields:
                :parent_locator: parent for new xblock, required for both duplicate and create new instance
                :duplicate_source_locator: if present, use this as the source for creating a duplicate copy
                :category: type of xblock, required if duplicate_source_locator is not present.
                :display_name: name for new xblock, optional
                :boilerplate: template name for populating fields, optional and only used
                     if duplicate_source_locator is not present
              The locator (unicode representation of a UsageKey) for the created xblock (minus children) is returned.
    """
    if usage_key_string:
        usage_key = usage_key_with_run(usage_key_string)

        access_check = has_studio_read_access if request.method == 'GET' else has_studio_write_access
        if not access_check(request.user, usage_key.course_key):
            raise PermissionDenied()

        if request.method == 'GET':
            accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

            if 'application/json' in accept_header:
                fields = request.REQUEST.get('fields', '').split(',')
                if 'graderType' in fields:
                    # right now can't combine output of this w/ output of _get_module_info, but worthy goal
                    return JsonResponse(CourseGradingModel.get_section_grader_type(usage_key))
                # TODO: pass fields to _get_module_info and only return those
                with modulestore().bulk_operations(usage_key.course_key):
                    response = _get_module_info(_get_xblock(usage_key, request.user))
                return JsonResponse(response)
            else:
                return HttpResponse(status=406)

        elif request.method == 'DELETE':
            _delete_item(usage_key, request.user)
            return JsonResponse()
        else:  # Since we have a usage_key, we are updating an existing xblock.
            return _save_xblock(
                request.user,
                _get_xblock(usage_key, request.user),
                data=request.json.get('data'),
                children_strings=request.json.get('children'),
                metadata=request.json.get('metadata'),
                nullout=request.json.get('nullout'),
                grader_type=request.json.get('graderType'),
                publish=request.json.get('publish'),
            )
    elif request.method in ('PUT', 'POST'):
        if 'duplicate_source_locator' in request.json:
            parent_usage_key = usage_key_with_run(request.json['parent_locator'])
            duplicate_source_usage_key = usage_key_with_run(request.json['duplicate_source_locator'])

            source_course = duplicate_source_usage_key.course_key
            dest_course = parent_usage_key.course_key
            if (
                    not has_studio_write_access(request.user, dest_course) or
                    not has_studio_read_access(request.user, source_course)
            ):
                raise PermissionDenied()

            dest_usage_key = _duplicate_item(
                parent_usage_key,
                duplicate_source_usage_key,
                request.user,
                request.json.get('display_name'),
            )

            return JsonResponse({"locator": unicode(dest_usage_key), "courseKey": unicode(dest_usage_key.course_key)})
        else:
            return _create_item(request)
    else:
        return HttpResponseBadRequest(
            "Only instance creation is supported without a usage key.",
            content_type="text/plain"
        )


@require_http_methods(("GET"))
@login_required
@expect_json
def xblock_view_handler(request, usage_key_string, view_name):
    """
    The restful handler for requests for rendered xblock views.

    Returns a json object containing two keys:
        html: The rendered html of the view
        resources: A list of tuples where the first element is the resource hash, and
            the second is the resource description
    """
    usage_key = usage_key_with_run(usage_key_string)
    if not has_studio_read_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

    if 'application/json' in accept_header:
        store = modulestore()
        xblock = store.get_item(usage_key)
        container_views = ['container_preview', 'reorderable_container_child_preview', 'container_child_preview']

        # wrap the generated fragment in the xmodule_editor div so that the javascript
        # can bind to it correctly
        xblock.runtime.wrappers.append(partial(
            wrap_xblock,
            'StudioRuntime',
            usage_id_serializer=unicode,
            request_token=request_token(request),
        ))

        if view_name in (STUDIO_VIEW, VISIBILITY_VIEW):
            try:
                fragment = xblock.render(view_name)
            # catch exceptions indiscriminately, since after this point they escape the
            # dungeon and surface as uneditable, unsaveable, and undeletable
            # component-goblins.
            except Exception as exc:                          # pylint: disable=broad-except
                log.debug("Unable to render %s for %r", view_name, xblock, exc_info=True)
                fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))

        elif view_name in PREVIEW_VIEWS + container_views:
            is_pages_view = view_name == STUDENT_VIEW   # Only the "Pages" view uses student view in Studio
            can_edit = has_studio_write_access(request.user, usage_key.course_key)

            # Determine the items to be shown as reorderable. Note that the view
            # 'reorderable_container_child_preview' is only rendered for xblocks that
            # are being shown in a reorderable container, so the xblock is automatically
            # added to the list.
            reorderable_items = set()
            if view_name == 'reorderable_container_child_preview':
                reorderable_items.add(xblock.location)

            paging = None
            try:
                if request.REQUEST.get('enable_paging', 'false') == 'true':
                    paging = {
                        'page_number': int(request.REQUEST.get('page_number', 0)),
                        'page_size': int(request.REQUEST.get('page_size', 0)),
                    }
            except ValueError:
                return HttpResponse(
                    content="Couldn't parse paging parameters: enable_paging: "
                            "{0}, page_number: {1}, page_size: {2}".format(
                                request.REQUEST.get('enable_paging', 'false'),
                                request.REQUEST.get('page_number', 0),
                                request.REQUEST.get('page_size', 0)
                            ),
                    status=400,
                    content_type="text/plain",
                )

            force_render = request.REQUEST.get('force_render', None)

            # Set up the context to be passed to each XBlock's render method.
            context = {
                'is_pages_view': is_pages_view,     # This setting disables the recursive wrapping of xblocks
                'is_unit_page': is_unit(xblock),
                'can_edit': can_edit,
                'root_xblock': xblock if (view_name == 'container_preview') else None,
                'reorderable_items': reorderable_items,
                'paging': paging,
                'force_render': force_render,
            }

            fragment = get_preview_fragment(request, xblock, context)

            # Note that the container view recursively adds headers into the preview fragment,
            # so only the "Pages" view requires that this extra wrapper be included.
            if is_pages_view:
                fragment.content = render_to_string('component.html', {
                    'xblock_context': context,
                    'xblock': xblock,
                    'locator': usage_key,
                    'preview': fragment.content,
                    'label': xblock.display_name or xblock.scope_ids.block_type,
                })
        else:
            raise Http404

        hashed_resources = OrderedDict()
        for resource in fragment.resources:
            hashed_resources[hash_resource(resource)] = resource._asdict()

        return JsonResponse({
            'html': fragment.content,
            'resources': hashed_resources.items()
        })

    else:
        return HttpResponse(status=406)


@require_http_methods(("GET"))
@login_required
@expect_json
def xblock_outline_handler(request, usage_key_string):
    """
    The restful handler for requests for XBlock information about the block and its children.
    This is used by the course outline in particular to construct the tree representation of
    a course.
    """
    usage_key = usage_key_with_run(usage_key_string)
    if not has_studio_read_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        store = modulestore()
        with store.bulk_operations(usage_key.course_key):
            root_xblock = store.get_item(usage_key, depth=None)
            return JsonResponse(create_xblock_info(
                root_xblock,
                include_child_info=True,
                course_outline=True,
                include_children_predicate=lambda xblock: not xblock.category == 'vertical'
            ))
    else:
        return Http404


@require_http_methods(("GET"))
@login_required
@expect_json
def xblock_container_handler(request, usage_key_string):
    """
    The restful handler for requests for XBlock information about the block and its children.
    This is used by the container page in particular to get additional information about publish state
    and ancestor state.
    """
    usage_key = usage_key_with_run(usage_key_string)

    if not has_studio_read_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        with modulestore().bulk_operations(usage_key.course_key):
            response = _get_module_info(
                _get_xblock(usage_key, request.user), include_ancestor_info=True, include_publishing_info=True
            )
        return JsonResponse(response)
    else:
        return Http404


def _update_with_callback(xblock, user, old_metadata=None, old_content=None):
    """
    Updates the xblock in the modulestore.
    But before doing so, it calls the xblock's editor_saved callback function.
    """
    if callable(getattr(xblock, "editor_saved", None)):
        if old_metadata is None:
            old_metadata = own_metadata(xblock)
        if old_content is None:
            old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)
        xblock.editor_saved(user, old_metadata, old_content)

    # Update after the callback so any changes made in the callback will get persisted.
    return modulestore().update_item(xblock, user.id)


def _save_xblock(user, xblock, data=None, children_strings=None, metadata=None, nullout=None,
                 grader_type=None, publish=None):
    """
    Saves xblock w/ its fields. Has special processing for grader_type, publish, and nullout and Nones in metadata.
    nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
    to default).
    """
    store = modulestore()
    # Perform all xblock changes within a (single-versioned) transaction
    with store.bulk_operations(xblock.location.course_key):

        # Don't allow updating an xblock and discarding changes in a single operation (unsupported by UI).
        if publish == "discard_changes":
            store.revert_to_published(xblock.location, user.id)
            # Returning the same sort of result that we do for other save operations. In the future,
            # we may want to return the full XBlockInfo.
            return JsonResponse({'id': unicode(xblock.location)})

        old_metadata = own_metadata(xblock)
        old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)

        if data:
            # TODO Allow any scope.content fields not just "data" (exactly like the get below this)
            xblock.data = data
        else:
            data = old_content['data'] if 'data' in old_content else None

        if children_strings is not None:
            children = []
            for child_string in children_strings:
                children.append(usage_key_with_run(child_string))

            # if new children have been added, remove them from their old parents
            new_children = set(children) - set(xblock.children)
            for new_child in new_children:
                old_parent_location = store.get_parent_location(new_child)
                if old_parent_location:
                    old_parent = store.get_item(old_parent_location)
                    old_parent.children.remove(new_child)
                    old_parent = _update_with_callback(old_parent, user)
                else:
                    # the Studio UI currently doesn't present orphaned children, so assume this is an error
                    return JsonResponse({"error": "Invalid data, possibly caused by concurrent authors."}, 400)

            # make sure there are no old children that became orphans
            # In a single-author (no-conflict) scenario, all children in the persisted list on the server should be
            # present in the updated list.  If there are any children that have been dropped as part of this update,
            # then that would be an error.
            #
            # We can be even more restrictive in a multi-author (conflict), by returning an error whenever
            # len(old_children) > 0. However, that conflict can still be "merged" if the dropped child had been
            # re-parented. Hence, the check for the parent in the any statement below.
            #
            # Note that this multi-author conflict error should not occur in modulestores (such as Split) that support
            # atomic write transactions.  In Split, if there was another author who moved one of the "old_children"
            # into another parent, then that child would have been deleted from this parent on the server. However,
            # this is error could occur in modulestores (such as Draft) that do not support atomic write-transactions
            old_children = set(xblock.children) - set(children)
            if any(
                    store.get_parent_location(old_child) == xblock.location
                    for old_child in old_children
            ):
                # since children are moved as part of a single transaction, orphans should not be created
                return JsonResponse({"error": "Invalid data, possibly caused by concurrent authors."}, 400)

            # set the children on the xblock
            xblock.children = children

        # also commit any metadata which might have been passed along
        if nullout is not None or metadata is not None:
            # the postback is not the complete metadata, as there's system metadata which is
            # not presented to the end-user for editing. So let's use the original (existing_item) and
            # 'apply' the submitted metadata, so we don't end up deleting system metadata.
            if nullout is not None:
                for metadata_key in nullout:
                    setattr(xblock, metadata_key, None)

            # update existing metadata with submitted metadata (which can be partial)
            # IMPORTANT NOTE: if the client passed 'null' (None) for a piece of metadata that means 'remove it'. If
            # the intent is to make it None, use the nullout field
            if metadata is not None:
                for metadata_key, value in metadata.items():
                    field = xblock.fields[metadata_key]

                    if value is None:
                        field.delete_from(xblock)
                    else:
                        try:
                            value = field.from_json(value)
                        except ValueError as verr:
                            reason = _("Invalid data")
                            if verr.message:
                                reason = _("Invalid data ({details})").format(details=verr.message)
                            return JsonResponse({"error": reason}, 400)

                        field.write_to(xblock, value)

        # update the xblock and call any xblock callbacks
        xblock = _update_with_callback(xblock, user, old_metadata, old_content)

        # for static tabs, their containing course also records their display name
        if xblock.location.category == 'static_tab':
            course = store.get_course(xblock.location.course_key)
            # find the course's reference to this tab and update the name.
            static_tab = CourseTabList.get_tab_by_slug(course.tabs, xblock.location.name)
            # only update if changed
            if static_tab and static_tab['name'] != xblock.display_name:
                static_tab['name'] = xblock.display_name
                store.update_item(course, user.id)

        result = {
            'id': unicode(xblock.location),
            'data': data,
            'metadata': own_metadata(xblock)
        }

        if grader_type is not None:
            result.update(CourseGradingModel.update_section_grader_type(xblock, grader_type, user))

        # If publish is set to 'republish' and this item is not in direct only categories and has previously been published,
        # then this item should be republished. This is used by staff locking to ensure that changing the draft
        # value of the staff lock will also update the published version, but only at the unit level.
        if publish == 'republish' and xblock.category not in DIRECT_ONLY_CATEGORIES:
            if modulestore().has_published_version(xblock):
                publish = 'make_public'

        # Make public after updating the xblock, in case the caller asked for both an update and a publish.
        # Used by Bok Choy tests and by republishing of staff locks.
        if publish == 'make_public':
            modulestore().publish(xblock.location, user.id)

        # Note that children aren't being returned until we have a use case.
        return JsonResponse(result, encoder=EdxJSONEncoder)


@login_required
@expect_json
def create_item(request):
    """
    Exposes internal helper method without breaking existing bindings/dependencies
    """
    return _create_item(request)


@login_required
@expect_json
def _create_item(request):
    """View for create items."""
    parent_locator = request.json['parent_locator']
    usage_key = usage_key_with_run(parent_locator)
    if not has_studio_write_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    category = request.json['category']
    if isinstance(usage_key, LibraryUsageLocator):
        # Only these categories are supported at this time.
        if category not in ['html', 'problem', 'video']:
            return HttpResponseBadRequest(
                "Category '%s' not supported for Libraries" % category, content_type='text/plain'
            )

    created_block = create_xblock(
        parent_locator=parent_locator,
        user=request.user,
        category=category,
        display_name=request.json.get('display_name'),
        boilerplate=request.json.get('boilerplate')
    )

    return JsonResponse(
        {"locator": unicode(created_block.location), "courseKey": unicode(created_block.location.course_key)}
    )


def _duplicate_item(parent_usage_key, duplicate_source_usage_key, user, display_name=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_usage_key.
    """
    store = modulestore()
    with store.bulk_operations(duplicate_source_usage_key.course_key):
        source_item = store.get_item(duplicate_source_usage_key)
        # Change the blockID to be unique.
        dest_usage_key = source_item.location.replace(name=uuid4().hex)
        category = dest_usage_key.block_type

        # Update the display name to indicate this is a duplicate (unless display name provided).
        # Can't use own_metadata(), b/c it converts data for JSON serialization -
        # not suitable for setting metadata of the new block
        duplicate_metadata = {}
        for field in source_item.fields.values():
            if field.scope == Scope.settings and field.is_set_on(source_item):
                duplicate_metadata[field.name] = field.read_from(source_item)
        if display_name is not None:
            duplicate_metadata['display_name'] = display_name
        else:
            if source_item.display_name is None:
                duplicate_metadata['display_name'] = _("Duplicate of {0}").format(source_item.category)
            else:
                duplicate_metadata['display_name'] = _("Duplicate of '{0}'").format(source_item.display_name)

        dest_module = store.create_item(
            user.id,
            dest_usage_key.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=source_item.get_explicitly_set_fields_by_scope(Scope.content),
            metadata=duplicate_metadata,
            runtime=source_item.runtime,
        )

        children_handled = False

        if hasattr(dest_module, 'studio_post_duplicate'):
            # Allow an XBlock to do anything fancy it may need to when duplicated from another block.
            # These blocks may handle their own children or parenting if needed. Let them return booleans to
            # let us know if we need to handle these or not.
            children_handled = dest_module.studio_post_duplicate(store, source_item)

        # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
        # Because DAGs are not fully supported, we need to actually duplicate each child as well.
        if source_item.has_children and not children_handled:
            dest_module.children = dest_module.children or []
            for child in source_item.children:
                dupe = _duplicate_item(dest_module.location, child, user=user)
                if dupe not in dest_module.children:  # _duplicate_item may add the child for us.
                    dest_module.children.append(dupe)
            store.update_item(dest_module, user.id)

        # pylint: disable=protected-access
        if 'detached' not in source_item.runtime.load_block_type(category)._class_tags:
            parent = store.get_item(parent_usage_key)
            # If source was already a child of the parent, add duplicate immediately afterward.
            # Otherwise, add child to end.
            if source_item.location in parent.children:
                source_index = parent.children.index(source_item.location)
                parent.children.insert(source_index + 1, dest_module.location)
            else:
                parent.children.append(dest_module.location)
            store.update_item(parent, user.id)

        return dest_module.location


@login_required
@expect_json
def delete_item(request, usage_key):
    """
    Exposes internal helper method without breaking existing bindings/dependencies
    """
    _delete_item(usage_key, request.user)


def _delete_item(usage_key, user):
    """
    Deletes an existing xblock with the given usage_key.
    If the xblock is a Static Tab, removes it from course.tabs as well.
    """
    store = modulestore()

    with store.bulk_operations(usage_key.course_key):
        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if usage_key.category == 'static_tab':

            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=(
                    "location:_delete_item_static_tab",
                    u"course:{}".format(unicode(usage_key.course_key)),
                )
            )

            course = store.get_course(usage_key.course_key)
            existing_tabs = course.tabs or []
            course.tabs = [tab for tab in existing_tabs if tab.get('url_slug') != usage_key.name]
            store.update_item(course, user.id)

        store.delete_item(usage_key, user.id)


@login_required
@require_http_methods(("GET", "DELETE"))
def orphan_handler(request, course_key_string):
    """
    View for handling orphan related requests. GET gets all of the current orphans.
    DELETE removes all orphans (requires is_staff access)

    An orphan is a block whose category is not in the DETACHED_CATEGORY list, is not the root, and is not reachable
    from the root via children
    """
    course_usage_key = CourseKey.from_string(course_key_string)
    if request.method == 'GET':
        if has_studio_read_access(request.user, course_usage_key):
            return JsonResponse([unicode(item) for item in modulestore().get_orphans(course_usage_key)])
        else:
            raise PermissionDenied()
    if request.method == 'DELETE':
        if request.user.is_staff:
            deleted_items = _delete_orphans(course_usage_key, request.user.id, commit=True)
            return JsonResponse({'deleted': deleted_items})
        else:
            raise PermissionDenied()


def _delete_orphans(course_usage_key, user_id, commit=False):
    """
    Helper function to delete orphans for a given course.
    If `commit` is False, this function does not actually remove
    the orphans.
    """
    store = modulestore()
    items = store.get_orphans(course_usage_key)
    branch = course_usage_key.branch
    if commit:
        with store.bulk_operations(course_usage_key):
            for itemloc in items:
                revision = ModuleStoreEnum.RevisionOption.all
                # specify branches when deleting orphans
                if branch == ModuleStoreEnum.BranchName.published:
                    revision = ModuleStoreEnum.RevisionOption.published_only
                store.delete_item(itemloc, user_id, revision=revision)
    return [unicode(item) for item in items]


def _get_xblock(usage_key, user):
    """
    Returns the xblock for the specified usage key. Note: if failing to find a key with a category
    in the CREATE_IF_NOT_FOUND list, an xblock will be created and saved automatically.
    """
    store = modulestore()
    with store.bulk_operations(usage_key.course_key):
        try:
            return store.get_item(usage_key, depth=None)
        except ItemNotFoundError:
            if usage_key.category in CREATE_IF_NOT_FOUND:
                # Create a new one for certain categories only. Used for course info handouts.
                return store.create_item(user.id, usage_key.course_key, usage_key.block_type, block_id=usage_key.block_id)
            else:
                raise
        except InvalidLocationError:
            log.error("Can't find item by location.")
            return JsonResponse({"error": "Can't find item by location: " + unicode(usage_key)}, 404)


def _get_module_info(xblock, rewrite_static_links=True, include_ancestor_info=False, include_publishing_info=False):
    """
    metadata, data, id representation of a leaf module fetcher.
    :param usage_key: A UsageKey
    """
    with modulestore().bulk_operations(xblock.location.course_key):
        data = getattr(xblock, 'data', '')
        if rewrite_static_links:
            data = replace_static_urls(
                data,
                None,
                course_id=xblock.location.course_key
            )

        # Pre-cache has changes for the entire course because we'll need it for the ancestor info
        # Except library blocks which don't [yet] use draft/publish
        if not isinstance(xblock.location, LibraryUsageLocator):
            modulestore().has_changes(modulestore().get_course(xblock.location.course_key, depth=None))

        # Note that children aren't being returned until we have a use case.
        xblock_info = create_xblock_info(
            xblock, data=data, metadata=own_metadata(xblock), include_ancestor_info=include_ancestor_info
        )
        if include_publishing_info:
            add_container_page_publishing_info(xblock, xblock_info)
        return xblock_info


def create_xblock_info(xblock, data=None, metadata=None, include_ancestor_info=False, include_child_info=False,
                       course_outline=False, include_children_predicate=NEVER, parent_xblock=None, graders=None,
                       user=None, course=None):
    """
    Creates the information needed for client-side XBlockInfo.

    If data or metadata are not specified, their information will not be added
    (regardless of whether or not the xblock actually has data or metadata).

    There are three optional boolean parameters:
      include_ancestor_info - if true, ancestor info is added to the response
      include_child_info - if true, direct child info is included in the response
      course_outline - if true, the xblock is being rendered on behalf of the course outline.
        There are certain expensive computations that do not need to be included in this case.

    In addition, an optional include_children_predicate argument can be provided to define whether or
    not a particular xblock should have its children included.
    """
    is_library_block = isinstance(xblock.location, LibraryUsageLocator)
    is_xblock_unit = is_unit(xblock, parent_xblock)
    # this should not be calculated for Sections and Subsections on Unit page or for library blocks
    has_changes = None
    if (is_xblock_unit or course_outline) and not is_library_block:
        has_changes = modulestore().has_changes(xblock)

    if graders is None:
        if not is_library_block:
            graders = CourseGradingModel.fetch(xblock.location.course_key).graders
        else:
            graders = []

    # Filter the graders data as needed
    graders = _filter_entrance_exam_grader(graders)

    # We need to load the course in order to retrieve user partition information.
    # For this reason, we load the course once and re-use it when recursively loading children.
    if course is None:
        course = modulestore().get_course(xblock.location.course_key)

    # Compute the child info first so it can be included in aggregate information for the parent
    should_visit_children = include_child_info and (course_outline and not is_xblock_unit or not course_outline)
    if should_visit_children and xblock.has_children:
        child_info = _create_xblock_child_info(
            xblock,
            course_outline,
            graders,
            include_children_predicate=include_children_predicate,
            user=user,
            course=course
        )
    else:
        child_info = None

    release_date = _get_release_date(xblock, user)

    if xblock.category != 'course':
        visibility_state = _compute_visibility_state(xblock, child_info, is_xblock_unit and has_changes)
    else:
        visibility_state = None
    published = modulestore().has_published_version(xblock) if not is_library_block else None

    # defining the default value 'True' for delete, drag and add new child actions in xblock_actions for each xblock.
    xblock_actions = {'deletable': True, 'draggable': True, 'childAddable': True}
    explanatory_message = None

    # is_entrance_exam is inherited metadata.
    if xblock.category == 'chapter' and getattr(xblock, "is_entrance_exam", None):
        # Entrance exam section should not be deletable, draggable and not have 'New Subsection' button.
        xblock_actions['deletable'] = xblock_actions['childAddable'] = xblock_actions['draggable'] = False
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)

        # Translators: The {pct_sign} here represents the percent sign, i.e., '%'
        # in many languages. This is used to avoid Transifex's misinterpreting of
        # '% o'. The percent sign is also translatable as a standalone string.
        explanatory_message = _('Students must score {score}{pct_sign} or higher to access course materials.').format(
            score=int(parent_xblock.entrance_exam_minimum_score_pct * 100),
            # Translators: This is the percent sign. It will be used to represent
            # a percent value out of 100, e.g. "58%" means "58/100".
            pct_sign=_('%'))

    xblock_info = {
        "id": unicode(xblock.location),
        "display_name": xblock.display_name_with_default,
        "category": xblock.category,
        "edited_on": get_default_time_display(xblock.subtree_edited_on) if xblock.subtree_edited_on else None,
        "published": published,
        "published_on": get_default_time_display(xblock.published_on) if published and xblock.published_on else None,
        "studio_url": xblock_studio_url(xblock, parent_xblock),
        "released_to_students": datetime.now(UTC) > xblock.start,
        "release_date": release_date,
        "visibility_state": visibility_state,
        "has_explicit_staff_lock": xblock.fields['visible_to_staff_only'].is_set_on(xblock),
        "start": xblock.fields['start'].to_json(xblock.start),
        "graded": xblock.graded,
        "due_date": get_default_time_display(xblock.due),
        "due": xblock.fields['due'].to_json(xblock.due),
        "format": xblock.format,
        "course_graders": [grader.get('type') for grader in graders],
        "has_changes": has_changes,
        "actions": xblock_actions,
        "explanatory_message": explanatory_message,
        "group_access": xblock.group_access,
        "user_partitions": get_user_partition_info(xblock, course=course),
    }

    # update xblock_info with special exam information if the feature flag is enabled
    if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
        if xblock.category == 'course':
            xblock_info.update({
                "enable_proctored_exams": xblock.enable_proctored_exams,
                "enable_timed_exams": xblock.enable_timed_exams
            })
        elif xblock.category == 'sequential':
            xblock_info.update({
                "is_proctored_exam": xblock.is_proctored_exam,
                "is_practice_exam": xblock.is_practice_exam,
                "is_time_limited": xblock.is_time_limited,
                "default_time_limit_minutes": xblock.default_time_limit_minutes
            })

    # Entrance exam subsection should be hidden. in_entrance_exam is inherited metadata, all children will have it.
    if xblock.category == 'sequential' and getattr(xblock, "in_entrance_exam", False):
        xblock_info["is_header_visible"] = False

    if data is not None:
        xblock_info["data"] = data
    if metadata is not None:
        xblock_info["metadata"] = metadata
    if include_ancestor_info:
        xblock_info['ancestor_info'] = _create_xblock_ancestor_info(xblock, course_outline)
    if child_info:
        xblock_info['child_info'] = child_info
    if visibility_state == VisibilityState.staff_only:
        xblock_info["ancestor_has_staff_lock"] = ancestor_has_staff_lock(xblock, parent_xblock)
    else:
        xblock_info["ancestor_has_staff_lock"] = False

    if course_outline:
        if xblock_info["has_explicit_staff_lock"]:
            xblock_info["staff_only_message"] = True
        elif child_info and child_info["children"]:
            xblock_info["staff_only_message"] = all([child["staff_only_message"] for child in child_info["children"]])
        else:
            xblock_info["staff_only_message"] = False

    return xblock_info


def add_container_page_publishing_info(xblock, xblock_info):  # pylint: disable=invalid-name
    """
    Adds information about the xblock's publish state to the supplied
    xblock_info for the container page.
    """
    def safe_get_username(user_id):
        """
        Guard against bad user_ids, like the infamous "**replace_user**".
        Note that this will ignore our special known IDs (ModuleStoreEnum.UserID).
        We should consider adding special handling for those values.

        :param user_id: the user id to get the username of
        :return: username, or None if the user does not exist or user_id is None
        """
        if user_id:
            try:
                return User.objects.get(id=user_id).username
            except:  # pylint: disable=bare-except
                pass

        return None

    xblock_info["edited_by"] = safe_get_username(xblock.subtree_edited_by)
    xblock_info["published_by"] = safe_get_username(xblock.published_by)
    xblock_info["currently_visible_to_students"] = is_currently_visible_to_students(xblock)
    xblock_info["has_content_group_components"] = has_children_visible_to_specific_content_groups(xblock)
    if xblock_info["release_date"]:
        xblock_info["release_date_from"] = _get_release_date_from(xblock)
    if xblock_info["visibility_state"] == VisibilityState.staff_only:
        xblock_info["staff_lock_from"] = _get_staff_lock_from(xblock)
    else:
        xblock_info["staff_lock_from"] = None


class VisibilityState(object):
    """
    Represents the possible visibility states for an xblock:

      live - the block and all of its descendants are live to students (excluding staff only items)
        Note: Live means both published and released.

      ready - the block is ready to go live and all of its descendants are live or ready (excluding staff only items)
        Note: content is ready when it is published and scheduled with a release date in the future.

      unscheduled - the block and all of its descendants have no release date (excluding staff only items)
        Note: it is valid for items to be published with no release date in which case they are still unscheduled.

      needs_attention - the block or its descendants are not fully live, ready or unscheduled (excluding staff only items)
        For example: one subsection has draft content, or there's both unreleased and released content in one section.

      staff_only - all of the block's content is to be shown to staff only
        Note: staff only items do not affect their parent's state.
    """
    live = 'live'
    ready = 'ready'
    unscheduled = 'unscheduled'
    needs_attention = 'needs_attention'
    staff_only = 'staff_only'


def _compute_visibility_state(xblock, child_info, is_unit_with_changes):
    """
    Returns the current publish state for the specified xblock and its children
    """
    if xblock.visible_to_staff_only:
        return VisibilityState.staff_only
    elif is_unit_with_changes:
        # Note that a unit that has never been published will fall into this category,
        # as well as previously published units with draft content.
        return VisibilityState.needs_attention
    is_unscheduled = xblock.start == DEFAULT_START_DATE
    is_live = datetime.now(UTC) > xblock.start
    children = child_info and child_info.get('children', [])
    if children and len(children) > 0:
        all_staff_only = True
        all_unscheduled = True
        all_live = True
        for child in child_info['children']:
            child_state = child['visibility_state']
            if child_state == VisibilityState.needs_attention:
                return child_state
            elif not child_state == VisibilityState.staff_only:
                all_staff_only = False
                if not child_state == VisibilityState.unscheduled:
                    all_unscheduled = False
                    if not child_state == VisibilityState.live:
                        all_live = False
        if all_staff_only:
            return VisibilityState.staff_only
        elif all_unscheduled:
            return VisibilityState.unscheduled if is_unscheduled else VisibilityState.needs_attention
        elif all_live:
            return VisibilityState.live if is_live else VisibilityState.needs_attention
        else:
            return VisibilityState.ready if not is_unscheduled else VisibilityState.needs_attention
    if is_unscheduled:
        return VisibilityState.unscheduled
    elif is_live:
        return VisibilityState.live
    else:
        return VisibilityState.ready


def _create_xblock_ancestor_info(xblock, course_outline):
    """
    Returns information about the ancestors of an xblock. Note that the direct parent will also return
    information about all of its children.
    """
    ancestors = []

    def collect_ancestor_info(ancestor, include_child_info=False):
        """
        Collect xblock info regarding the specified xblock and its ancestors.
        """
        if ancestor:
            direct_children_only = lambda parent: parent == ancestor
            ancestors.append(create_xblock_info(
                ancestor,
                include_child_info=include_child_info,
                course_outline=course_outline,
                include_children_predicate=direct_children_only
            ))
            collect_ancestor_info(get_parent_xblock(ancestor))
    collect_ancestor_info(get_parent_xblock(xblock), include_child_info=True)
    return {
        'ancestors': ancestors
    }


def _create_xblock_child_info(xblock, course_outline, graders, include_children_predicate=NEVER, user=None, course=None):  # pylint: disable=line-too-long
    """
    Returns information about the children of an xblock, as well as about the primary category
    of xblock expected as children.
    """
    child_info = {}
    child_category = xblock_primary_child_category(xblock)
    if child_category:
        child_info = {
            'category': child_category,
            'display_name': xblock_type_display_name(child_category, default_display_name=child_category),
        }
    if xblock.has_children and include_children_predicate(xblock):
        child_info['children'] = [
            create_xblock_info(
                child, include_child_info=True, course_outline=course_outline,
                include_children_predicate=include_children_predicate,
                parent_xblock=xblock,
                graders=graders,
                user=user,
                course=course,
            ) for child in xblock.get_children()
        ]
    return child_info


def _get_release_date(xblock, user=None):
    """
    Returns the release date for the xblock, or None if the release date has never been set.
    """
    # If year of start date is less than 1900 then reset the start date to DEFAULT_START_DATE
    reset_to_default = False
    try:
        reset_to_default = xblock.start.year < 1900
    except ValueError:
        # For old mongo courses, accessing the start attribute calls `to_json()`,
        # which raises a `ValueError` for years < 1900.
        reset_to_default = True

    if reset_to_default and user:
        xblock.start = DEFAULT_START_DATE
        xblock = _update_with_callback(xblock, user)

    # Treat DEFAULT_START_DATE as a magic number that means the release date has not been set
    return get_default_time_display(xblock.start) if xblock.start != DEFAULT_START_DATE else None


def _get_release_date_from(xblock):
    """
    Returns a string representation of the section or subsection that sets the xblock's release date
    """
    return _xblock_type_and_display_name(find_release_date_source(xblock))


def _get_staff_lock_from(xblock):
    """
    Returns a string representation of the section or subsection that sets the xblock's release date
    """
    source = find_staff_lock_source(xblock)
    return _xblock_type_and_display_name(source) if source else None


def _xblock_type_and_display_name(xblock):
    """
    Returns a string representation of the xblock's type and display name
    """
    return _('{section_or_subsection} "{display_name}"').format(
        section_or_subsection=xblock_type_display_name(xblock),
        display_name=xblock.display_name_with_default)
