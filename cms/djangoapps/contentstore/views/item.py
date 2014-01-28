"""Views for items (modules)."""

import hashlib
import logging
from uuid import uuid4

from collections import OrderedDict
from functools import partial
from static_replace import replace_static_urls
from xmodule_modifiers import wrap_xblock

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from xblock.fields import Scope
from xblock.fragment import Fragment
from xblock.core import XBlock

import xmodule.x_module
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore import Location
from xmodule.x_module import prefer_xmodules
from xmodule.util.transcripts_utils import manage_video_subtitles_save

from util.json_request import expect_json, JsonResponse
from util.string_utils import str_to_bool

from ..utils import get_modulestore

from .access import has_course_access
from .helpers import _xmodule_recurse
from contentstore.views.preview import get_preview_fragment
from edxmako.shortcuts import render_to_string
from models.settings.course_grading import CourseGradingModel
from cms.lib.xblock.runtime import handler_url

__all__ = ['orphan_handler', 'xblock_handler']

log = logging.getLogger(__name__)

CREATE_IF_NOT_FOUND = ['course_info']


# In order to allow descriptors to use a handler url, we need to
# monkey-patch the x_module library.
# TODO: Remove this code when Runtimes are no longer created by modulestores
xmodule.x_module.descriptor_global_handler_url = handler_url


def hash_resource(resource):
    """
    Hash a :class:`xblock.fragment.FragmentResource
    """
    md5 = hashlib.md5()
    for data in resource:
        md5.update(data)
    return md5.hexdigest()


# pylint: disable=unused-argument
@require_http_methods(("DELETE", "GET", "PUT", "POST"))
@login_required
@expect_json
def xblock_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for xblock requests.

    DELETE
        json: delete this xblock instance from the course. Supports query parameters "recurse" to delete
        all children and "all_versions" to delete from all (mongo) versions.
    GET
        json: returns representation of the xblock (locator id, data, and metadata).
              if ?fields=graderType, it returns the graderType for the unit instead of the above.
        html: returns HTML for rendering the xblock (which includes both the "preview" view and the "editor" view)
    PUT or POST
        json: if xblock locator is specified, update the xblock instance. The json payload can contain
              these fields, all optional:
                :data: the new value for the data.
                :children: the locator ids of children for this xblock.
                :metadata: new values for the metadata fields. Any whose values are None will be deleted not set
                       to None! Absent ones will be left alone.
                :nullout: which metadata fields to set to None
                :graderType: change how this unit is graded
                :publish: can be one of three values, 'make_public, 'make_private', or 'create_draft'
              The JSON representation on the updated xblock (minus children) is returned.

              if xblock locator is not specified, create a new xblock instance, either by duplicating
              an existing xblock, or creating an entirely new one. The json playload can contain
              these fields:
                :parent_locator: parent for new xblock, required for both duplicate and create new instance
                :duplicate_source_locator: if present, use this as the source for creating a duplicate copy
                :category: type of xblock, required if duplicate_source_locator is not present.
                :display_name: name for new xblock, optional
                :boilerplate: template name for populating fields, optional and only used
                     if duplicate_source_locator is not present
              The locator (and old-style id) for the created xblock (minus children) is returned.
    """
    if package_id is not None:
        locator = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
        if not has_course_access(request.user, locator):
            raise PermissionDenied()
        old_location = loc_mapper().translate_locator_to_location(locator)

        if request.method == 'GET':
            accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

            if 'application/x-fragment+json' in accept_header:
                component = modulestore().get_item(old_location)

                # Wrap the generated fragment in the xmodule_editor div so that the javascript
                # can bind to it correctly
                component.runtime.wrappers.append(partial(wrap_xblock, 'StudioRuntime'))

                try:
                    editor_fragment = component.render('studio_view')
                # catch exceptions indiscriminately, since after this point they escape the
                # dungeon and surface as uneditable, unsaveable, and undeletable
                # component-goblins.
                except Exception as exc:                          # pylint: disable=W0703
                    log.debug("Unable to render studio_view for %r", component, exc_info=True)
                    editor_fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))

                modulestore().save_xmodule(component)

                preview_fragment = get_preview_fragment(request, component)

                hashed_resources = OrderedDict()
                for resource in editor_fragment.resources + preview_fragment.resources:
                    hashed_resources[hash_resource(resource)] = resource

                return JsonResponse({
                    'html': render_to_string('component.html', {
                        'preview': preview_fragment.content,
                        'editor': editor_fragment.content,
                        'label': component.display_name or component.scope_ids.block_type,
                    }),
                    'resources': hashed_resources.items()
                })

            elif 'application/json' in accept_header:
                fields = request.REQUEST.get('fields', '').split(',')
                if 'graderType' in fields:
                    # right now can't combine output of this w/ output of _get_module_info, but worthy goal
                    return JsonResponse(CourseGradingModel.get_section_grader_type(locator))
                # TODO: pass fields to _get_module_info and only return those
                rsp = _get_module_info(locator)
                return JsonResponse(rsp)
            else:
                return HttpResponse(status=406)

        elif request.method == 'DELETE':
            delete_children = str_to_bool(request.REQUEST.get('recurse', 'False'))
            delete_all_versions = str_to_bool(request.REQUEST.get('all_versions', 'False'))

            return _delete_item_at_location(old_location, delete_children, delete_all_versions)
        else:  # Since we have a package_id, we are updating an existing xblock.
            return _save_item(
                request,
                locator,
                old_location,
                data=request.json.get('data'),
                children=request.json.get('children'),
                metadata=request.json.get('metadata'),
                nullout=request.json.get('nullout'),
                grader_type=request.json.get('graderType'),
                publish=request.json.get('publish'),
            )
    elif request.method in ('PUT', 'POST'):
        if 'duplicate_source_locator' in request.json:
            parent_locator = BlockUsageLocator(request.json['parent_locator'])
            duplicate_source_locator = BlockUsageLocator(request.json['duplicate_source_locator'])

            # _duplicate_item is dealing with locations to facilitate the recursive call for
            # duplicating children.
            parent_location = loc_mapper().translate_locator_to_location(parent_locator)
            duplicate_source_location = loc_mapper().translate_locator_to_location(duplicate_source_locator)
            dest_location = _duplicate_item(
                parent_location,
                duplicate_source_location,
                request.json.get('display_name')
            )
            course_location = loc_mapper().translate_locator_to_location(BlockUsageLocator(parent_locator), get_course=True)
            dest_locator = loc_mapper().translate_location(course_location.course_id, dest_location, False, True)
            return JsonResponse({"locator": unicode(dest_locator)})
        else:
            return _create_item(request)
    else:
        return HttpResponseBadRequest(
            "Only instance creation is supported without a package_id.",
            content_type="text/plain"
        )


def _save_item(request, usage_loc, item_location, data=None, children=None, metadata=None, nullout=None,
               grader_type=None, publish=None):
    """
    Saves xblock w/ its fields. Has special processing for grader_type, publish, and nullout and Nones in metadata.
    nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
    to default).

    The item_location is still the old-style location whereas usage_loc is a BlockUsageLocator
    """
    store = get_modulestore(item_location)

    try:
        existing_item = store.get_item(item_location)
    except ItemNotFoundError:
        if item_location.category in CREATE_IF_NOT_FOUND:
            # New module at this location, for pages that are not pre-created.
            # Used for course info handouts.
            store.create_and_save_xmodule(item_location)
            existing_item = store.get_item(item_location)
        else:
            raise
    except InvalidLocationError:
        log.error("Can't find item by location.")
        return JsonResponse({"error": "Can't find item by location: " + str(item_location)}, 404)

    if publish:
        if publish == 'make_private':
            _xmodule_recurse(existing_item, lambda i: modulestore().unpublish(i.location))
        elif publish == 'create_draft':
            # This clones the existing item location to a draft location (the draft is
            # implicit, because modulestore is a Draft modulestore)
            modulestore().convert_to_draft(item_location)

    if data:
        store.update_item(item_location, data)
    else:
        data = existing_item.get_explicitly_set_fields_by_scope(Scope.content)

    if children is not None:
        children_ids = [
            loc_mapper().translate_locator_to_location(BlockUsageLocator(child_locator)).url()
            for child_locator
            in children
        ]
        store.update_children(item_location, children_ids)

    # cdodge: also commit any metadata which might have been passed along
    if nullout is not None or metadata is not None:
        # the postback is not the complete metadata, as there's system metadata which is
        # not presented to the end-user for editing. So let's use the original (existing_item) and
        # 'apply' the submitted metadata, so we don't end up deleting system metadata.
        if nullout is not None:
            for metadata_key in nullout:
                setattr(existing_item, metadata_key, None)

        # update existing metadata with submitted metadata (which can be partial)
        # IMPORTANT NOTE: if the client passed 'null' (None) for a piece of metadata that means 'remove it'. If
        # the intent is to make it None, use the nullout field
        if metadata is not None:
            for metadata_key, value in metadata.items():
                field = existing_item.fields[metadata_key]

                if value is None:
                    field.delete_from(existing_item)
                else:
                    try:
                        value = field.from_json(value)
                    except ValueError:
                        return JsonResponse({"error": "Invalid data"}, 400)
                    field.write_to(existing_item, value)

        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        existing_item.save()
        # commit to datastore
        store.update_metadata(item_location, own_metadata(existing_item))

        if existing_item.category == 'video':
            manage_video_subtitles_save(existing_item, existing_item)

    result = {
        'id': unicode(usage_loc),
        'data': data,
        'metadata': own_metadata(existing_item)
    }

    if grader_type is not None:
        result.update(CourseGradingModel.update_section_grader_type(existing_item, grader_type))

    # Make public after updating the xblock, in case the caller asked
    # for both an update and a publish.
    if publish and publish == 'make_public':
        _xmodule_recurse(
            existing_item,
            lambda i: modulestore().publish(i.location, request.user.id)
        )

    # Note that children aren't being returned until we have a use case.
    return JsonResponse(result)


@login_required
@expect_json
def _create_item(request):
    """View for create items."""
    parent_locator = BlockUsageLocator(request.json['parent_locator'])
    parent_location = loc_mapper().translate_locator_to_location(parent_locator)
    category = request.json['category']

    display_name = request.json.get('display_name')

    if not has_course_access(request.user, parent_location):
        raise PermissionDenied()

    parent = get_modulestore(category).get_item(parent_location)
    dest_location = parent_location.replace(category=category, name=uuid4().hex)

    # get the metadata, display_name, and definition from the request
    metadata = {}
    data = None
    template_id = request.json.get('boilerplate')
    if template_id is not None:
        clz = parent.runtime.load_block_type(category)
        if clz is not None:
            template = clz.get_template(template_id)
            if template is not None:
                metadata = template.get('metadata', {})
                data = template.get('data')

    if display_name is not None:
        metadata['display_name'] = display_name

    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=data,
        metadata=metadata,
        system=parent.runtime,
    )

    # TODO replace w/ nicer accessor
    if not 'detached' in parent.runtime.load_block_type(category)._class_tags:
        get_modulestore(parent.location).update_children(parent_location, parent.children + [dest_location.url()])

    course_location = loc_mapper().translate_locator_to_location(parent_locator, get_course=True)
    locator = loc_mapper().translate_location(course_location.course_id, dest_location, False, True)
    return JsonResponse({"locator": unicode(locator)})


def _duplicate_item(parent_location, duplicate_source_location, display_name=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_location.
    """
    store = get_modulestore(duplicate_source_location)
    source_item = store.get_item(duplicate_source_location)
    # Change the blockID to be unique.
    dest_location = duplicate_source_location.replace(name=uuid4().hex)
    category = dest_location.category

    # Update the display name to indicate this is a duplicate (unless display name provided).
    duplicate_metadata = own_metadata(source_item)
    if display_name is not None:
        duplicate_metadata['display_name'] = display_name
    else:
        if source_item.display_name is None:
            duplicate_metadata['display_name'] = _("Duplicate of {0}").format(source_item.category)
        else:
            duplicate_metadata['display_name'] = _("Duplicate of '{0}'").format(source_item.display_name)

    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=source_item.data if hasattr(source_item, 'data') else None,
        metadata=duplicate_metadata,
        system=source_item.runtime,
    )

    # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
    # Because DAGs are not fully supported, we need to actually duplicate each child as well.
    if source_item.has_children:
        copied_children = []
        for child in source_item.children:
            copied_children.append(_duplicate_item(dest_location, Location(child)).url())
        get_modulestore(dest_location).update_children(dest_location, copied_children)

    if not 'detached' in source_item.runtime.load_block_type(category)._class_tags:
        parent = get_modulestore(parent_location).get_item(parent_location)
        # If source was already a child of the parent, add duplicate immediately afterward.
        # Otherwise, add child to end.
        if duplicate_source_location.url() in parent.children:
            source_index = parent.children.index(duplicate_source_location.url())
            parent.children.insert(source_index + 1, dest_location.url())
        else:
            parent.children.append(dest_location.url())
        get_modulestore(parent_location).update_children(parent_location, parent.children)

    return dest_location


def _delete_item_at_location(item_location, delete_children=False, delete_all_versions=False):
    """
    Deletes the item at with the given Location.

    It is assumed that course permissions have already been checked.
    """
    store = get_modulestore(item_location)

    item = store.get_item(item_location)

    if delete_children:
        _xmodule_recurse(item, lambda i: store.delete_item(i.location, delete_all_versions))
    else:
        store.delete_item(item.location, delete_all_versions)

    # cdodge: we need to remove our parent's pointer to us so that it is no longer dangling
    if delete_all_versions:
        parent_locs = modulestore('direct').get_parent_locations(item_location, None)

        for parent_loc in parent_locs:
            parent = modulestore('direct').get_item(parent_loc)
            item_url = item_location.url()
            if item_url in parent.children:
                children = parent.children
                children.remove(item_url)
                parent.children = children
                modulestore('direct').update_children(parent.location, parent.children)

    return JsonResponse()


# pylint: disable=W0613
@login_required
@require_http_methods(("GET", "DELETE"))
def orphan_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    View for handling orphan related requests. GET gets all of the current orphans.
    DELETE removes all orphans (requires is_staff access)

    An orphan is a block whose category is not in the DETACHED_CATEGORY list, is not the root, and is not reachable
    from the root via children

    :param request:
    :param package_id: Locator syntax package_id
    """
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    # DHM: when split becomes back-end, move or conditionalize this conversion
    old_location = loc_mapper().translate_locator_to_location(location)
    if request.method == 'GET':
        if has_course_access(request.user, old_location):
            return JsonResponse(modulestore().get_orphans(old_location, 'draft'))
        else:
            raise PermissionDenied()
    if request.method == 'DELETE':
        if request.user.is_staff:
            items = modulestore().get_orphans(old_location, 'draft')
            for item in items:
                modulestore('draft').delete_item(item, True)
            return JsonResponse({'deleted': items})
        else:
            raise PermissionDenied()


def _get_module_info(usage_loc, rewrite_static_links=True):
    """
    metadata, data, id representation of a leaf module fetcher.
    :param usage_loc: A BlockUsageLocator
    """
    old_location = loc_mapper().translate_locator_to_location(usage_loc)
    store = get_modulestore(old_location)
    try:
        module = store.get_item(old_location)
    except ItemNotFoundError:
        if old_location.category in CREATE_IF_NOT_FOUND:
            # Create a new one for certain categories only. Used for course info handouts.
            store.create_and_save_xmodule(old_location)
            module = store.get_item(old_location)
        else:
            raise

    data = getattr(module, 'data', '')
    if rewrite_static_links:
        # we pass a partially bogus course_id as we don't have the RUN information passed yet
        # through the CMS. Also the contentstore is also not RUN-aware at this point in time.
        data = replace_static_urls(
            data,
            None,
            course_id=module.location.org + '/' + module.location.course + '/BOGUS_RUN_REPLACE_WHEN_AVAILABLE'
        )

    # Note that children aren't being returned until we have a use case.
    return {
        'id': unicode(usage_loc),
        'data': data,
        'metadata': own_metadata(module)
    }
