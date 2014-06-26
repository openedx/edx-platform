"""Views for items (modules)."""
from __future__ import absolute_import

import hashlib
import logging
from uuid import uuid4

from collections import OrderedDict
from functools import partial
from static_replace import replace_static_urls
from xmodule_modifiers import wrap_xblock

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from xblock.fields import Scope
from xblock.fragment import Fragment

import xmodule
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError, DuplicateItemError
from xmodule.modulestore.inheritance import own_metadata
from xmodule.x_module import PREVIEW_VIEWS, STUDIO_VIEW, STUDENT_VIEW

from util.json_request import expect_json, JsonResponse
from util.string_utils import str_to_bool

from ..utils import get_modulestore

from .access import has_course_access
from .helpers import _xmodule_recurse
from contentstore.utils import compute_publish_state, PublishState
from django.contrib.auth.models import User
from util.date_utils import get_default_time_display
from contentstore.views.helpers import is_unit
from contentstore.views.preview import get_preview_fragment
from edxmako.shortcuts import render_to_string
from models.settings.course_grading import CourseGradingModel
from cms.lib.xblock.runtime import handler_url, local_resource_url
from opaque_keys.edx.keys import UsageKey, CourseKey

__all__ = ['orphan_handler', 'xblock_handler', 'xblock_view_handler']

log = logging.getLogger(__name__)

CREATE_IF_NOT_FOUND = ['course_info']


# In order to allow descriptors to use a handler url, we need to
# monkey-patch the x_module library.
# TODO: Remove this code when Runtimes are no longer created by modulestores
xmodule.x_module.descriptor_global_handler_url = handler_url
xmodule.x_module.descriptor_global_local_resource_url = local_resource_url


def hash_resource(resource):
    """
    Hash a :class:`xblock.fragment.FragmentResource`.
    """
    md5 = hashlib.md5()
    md5.update(repr(resource))
    return md5.hexdigest()


# pylint: disable=unused-argument
@require_http_methods(("DELETE", "GET", "PUT", "POST"))
@login_required
@expect_json
def xblock_handler(request, usage_key_string):
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
                :children: the unicode representation of the UsageKeys of children for this xblock.
                :metadata: new values for the metadata fields. Any whose values are None will be deleted not set
                       to None! Absent ones will be left alone.
                :nullout: which metadata fields to set to None
                :graderType: change how this unit is graded
                :publish: can be one of three values, 'make_public, 'make_private' TODO: delete all "create_draft" code
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
        usage_key = UsageKey.from_string(usage_key_string)
        if not has_course_access(request.user, usage_key.course_key):
            raise PermissionDenied()

        if request.method == 'GET':
            accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

            if 'application/json' in accept_header:
                fields = request.REQUEST.get('fields', '').split(',')
                if 'graderType' in fields:
                    # right now can't combine output of this w/ output of _get_module_info, but worthy goal
                    return JsonResponse(CourseGradingModel.get_section_grader_type(usage_key))
                # TODO: pass fields to _get_module_info and only return those
                rsp = _get_module_info(usage_key)
                return JsonResponse(rsp)
            else:
                return HttpResponse(status=406)

        elif request.method == 'DELETE':
            delete_children = str_to_bool(request.REQUEST.get('recurse', 'False'))
            delete_all_versions = str_to_bool(request.REQUEST.get('all_versions', 'False'))

            return _delete_item_at_location(usage_key, delete_children, delete_all_versions, request.user)
        else:  # Since we have a usage_key, we are updating an existing xblock.
            return _save_item(
                request,
                usage_key,
                data=request.json.get('data'),
                children=request.json.get('children'),
                metadata=request.json.get('metadata'),
                nullout=request.json.get('nullout'),
                grader_type=request.json.get('graderType'),
                publish=request.json.get('publish'),
            )
    elif request.method in ('PUT', 'POST'):
        if 'duplicate_source_locator' in request.json:
            parent_usage_key = UsageKey.from_string(request.json['parent_locator'])
            duplicate_source_usage_key = UsageKey.from_string(request.json['duplicate_source_locator'])

            dest_usage_key = _duplicate_item(
                parent_usage_key,
                duplicate_source_usage_key,
                request.json.get('display_name'),
                request.user,
            )

            return JsonResponse({"locator": unicode(dest_usage_key)})
        else:
            return _create_item(request)
    else:
        return HttpResponseBadRequest(
            "Only instance creation is supported without a usage key.",
            content_type="text/plain"
        )

# pylint: disable=unused-argument
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
    usage_key = UsageKey.from_string(usage_key_string)
    if not has_course_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

    if 'application/json' in accept_header:
        store = get_modulestore(usage_key)
        xblock = store.get_item(usage_key)
        is_read_only = _is_xblock_read_only(xblock)
        container_views = ['container_preview', 'reorderable_container_child_preview']

        # wrap the generated fragment in the xmodule_editor div so that the javascript
        # can bind to it correctly
        xblock.runtime.wrappers.append(partial(wrap_xblock, 'StudioRuntime', usage_id_serializer=unicode))

        if view_name == STUDIO_VIEW:
            try:
                fragment = xblock.render(STUDIO_VIEW)
            # catch exceptions indiscriminately, since after this point they escape the
            # dungeon and surface as uneditable, unsaveable, and undeletable
            # component-goblins.
            except Exception as exc:                          # pylint: disable=w0703
                log.debug("unable to render studio_view for %r", xblock, exc_info=True)
                fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))

            # change not authored by requestor but by xblocks.
            store.update_item(xblock, None)
        elif view_name in (PREVIEW_VIEWS + container_views):
            is_pages_view = view_name == STUDENT_VIEW   # Only the "Pages" view uses student view in Studio

            # Determine the items to be shown as reorderable. Note that the view
            # 'reorderable_container_child_preview' is only rendered for xblocks that
            # are being shown in a reorderable container, so the xblock is automatically
            # added to the list.
            reorderable_items = set()
            if view_name == 'reorderable_container_child_preview':
                reorderable_items.add(xblock.location)

            # Set up the context to be passed to each XBlock's render method.
            context = {
                'is_pages_view': is_pages_view,     # This setting disables the recursive wrapping of xblocks
                'is_unit_page': is_unit(xblock),
                'read_only': is_read_only,
                'root_xblock': xblock if (view_name == 'container_preview') else None,
                'reorderable_items': reorderable_items
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
            hashed_resources[hash_resource(resource)] = resource

        return JsonResponse({
            'html': fragment.content,
            'resources': hashed_resources.items()
        })

    else:
        return HttpResponse(status=406)


def _is_xblock_read_only(xblock):
    """
    Returns true if the specified xblock is read-only, meaning that it cannot be edited.
    """
    # We allow direct editing of xblocks in DIRECT_ONLY_CATEGORIES (for example, static pages).
    # if xblock.category in DIRECT_ONLY_CATEGORIES:
    #     return False
    # component_publish_state = compute_publish_state(xblock)
    # return component_publish_state == PublishState.public
    # TODO: correct with publishing story.
    return False


def _save_item(request, usage_key, data=None, children=None, metadata=None, nullout=None,
               grader_type=None, publish=None):
    """
    Saves xblock w/ its fields. Has special processing for grader_type, publish, and nullout and Nones in metadata.
    nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
    to default).
    """
    store = get_modulestore(usage_key)

    try:
        existing_item = store.get_item(usage_key)
    except ItemNotFoundError:
        if usage_key.category in CREATE_IF_NOT_FOUND:
            # New module at this location, for pages that are not pre-created.
            # Used for course info handouts.
            store.create_and_save_xmodule(usage_key)
            existing_item = store.get_item(usage_key)
        else:
            raise
    except InvalidLocationError:
        log.error("Can't find item by location.")
        return JsonResponse({"error": "Can't find item by location: " + unicode(usage_key)}, 404)

    old_metadata = own_metadata(existing_item)
    old_content = existing_item.get_explicitly_set_fields_by_scope(Scope.content)

    if data:
        # TODO Allow any scope.content fields not just "data" (exactly like the get below this)
        existing_item.data = data
    else:
        data = old_content['data'] if 'data' in old_content else None

    if children is not None:
        children_usage_keys = [
            UsageKey.from_string(child)
            for child
            in children
        ]
        existing_item.children = children_usage_keys

    # also commit any metadata which might have been passed along
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

    if callable(getattr(existing_item, "editor_saved", None)):
        existing_item.editor_saved(request.user, old_metadata, old_content)

    # commit to datastore
    store.update_item(existing_item, request.user.id)

    result = {
        'id': unicode(usage_key),
        'data': data,
        'metadata': own_metadata(existing_item)
    }

    if grader_type is not None:
        result.update(CourseGradingModel.update_section_grader_type(existing_item, grader_type, request.user))

    # Make public after updating the xblock, in case the caller asked
    # for both an update and a publish.
    if publish and publish == 'make_public':
        def _publish(block):
            # This is super gross, but prevents us from publishing something that
            # we shouldn't. Ideally, all modulestores would have a consistant
            # interface for publishing. However, as of now, only the DraftMongoModulestore
            # does, so we have to check for the attribute explicitly.
            store = get_modulestore(block.location)
            store.publish(block.location, request.user.id)

        _xmodule_recurse(
            existing_item,
            _publish
        )

    # Note that children aren't being returned until we have a use case.
    return JsonResponse(result)


@login_required
@expect_json
def _create_item(request):
    """View for create items."""
    usage_key = UsageKey.from_string(request.json['parent_locator'])
    category = request.json['category']

    display_name = request.json.get('display_name')

    if not has_course_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    parent = get_modulestore(category).get_item(usage_key)
    dest_usage_key = usage_key.replace(category=category, name=uuid4().hex)

    # get the metadata, display_name, and definition from the request
    metadata = {}
    data = None
    template_id = request.json.get('boilerplate')
    if template_id:
        clz = parent.runtime.load_block_type(category)
        if clz is not None:
            template = clz.get_template(template_id)
            if template is not None:
                metadata = template.get('metadata', {})
                data = template.get('data')

    if display_name is not None:
        metadata['display_name'] = display_name

    get_modulestore(category).create_and_save_xmodule(
        dest_usage_key,
        definition_data=data,
        metadata=metadata,
        system=parent.runtime,
        user_id=request.user.id
    )

    # TODO replace w/ nicer accessor
    if not 'detached' in parent.runtime.load_block_type(category)._class_tags:
        parent.children.append(dest_usage_key)
        get_modulestore(parent.location).update_item(parent, request.user.id)

    return JsonResponse({"locator": unicode(dest_usage_key), "courseKey": unicode(dest_usage_key.course_key)})


def _duplicate_item(parent_usage_key, duplicate_source_usage_key, display_name=None, user=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_usage_key.
    """
    store = get_modulestore(duplicate_source_usage_key)
    source_item = store.get_item(duplicate_source_usage_key)
    # Change the blockID to be unique.
    dest_usage_key = duplicate_source_usage_key.replace(name=uuid4().hex)
    category = dest_usage_key.category

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
        dest_usage_key,
        definition_data=source_item.data if hasattr(source_item, 'data') else None,
        metadata=duplicate_metadata,
        system=source_item.runtime,
    )

    dest_module = get_modulestore(category).get_item(dest_usage_key)
    # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
    # Because DAGs are not fully supported, we need to actually duplicate each child as well.
    if source_item.has_children:
        dest_module.children = []
        for child in source_item.children:
            dupe = _duplicate_item(dest_usage_key, child, user=user)
            dest_module.children.append(dupe)
        get_modulestore(dest_usage_key).update_item(dest_module, user.id if user else None)

    if not 'detached' in source_item.runtime.load_block_type(category)._class_tags:
        parent = get_modulestore(parent_usage_key).get_item(parent_usage_key)
        # If source was already a child of the parent, add duplicate immediately afterward.
        # Otherwise, add child to end.
        if duplicate_source_usage_key in parent.children:
            source_index = parent.children.index(duplicate_source_usage_key)
            parent.children.insert(source_index + 1, dest_usage_key)
        else:
            parent.children.append(dest_usage_key)
        get_modulestore(parent_usage_key).update_item(parent, user.id if user else None)

    return dest_usage_key


def _delete_item_at_location(item_usage_key, delete_children=False, delete_all_versions=False, user=None):
    """
    Deletes the item at with the given Location.

    It is assumed that course permissions have already been checked.
    """
    store = get_modulestore(item_usage_key)

    item = store.get_item(item_usage_key)

    if delete_children:
        _xmodule_recurse(item, lambda i: store.delete_item(i.location, delete_all_versions=delete_all_versions))
    else:
        store.delete_item(item.location, delete_all_versions=delete_all_versions)

    # cdodge: we need to remove our parent's pointer to us so that it is no longer dangling
    if delete_all_versions:
        parent_locs = modulestore('direct').get_parent_locations(item_usage_key)

        for parent_loc in parent_locs:
            parent = modulestore('direct').get_item(parent_loc)
            parent.children.remove(item_usage_key)
            modulestore('direct').update_item(parent, user.id if user else None)

    return JsonResponse()


# pylint: disable=W0613
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
        if has_course_access(request.user, course_usage_key):
            return JsonResponse(modulestore().get_orphans(course_usage_key))
        else:
            raise PermissionDenied()
    if request.method == 'DELETE':
        if request.user.is_staff:
            items = modulestore().get_orphans(course_usage_key)
            for itemloc in items:
                # get_orphans returns the deprecated string format
                usage_key = course_usage_key.make_usage_key_from_deprecated_string(itemloc)
                modulestore().delete_item(usage_key, delete_all_versions=True)
            return JsonResponse({'deleted': items})
        else:
            raise PermissionDenied()


def _get_module_info(usage_key, rewrite_static_links=True):
    """
    metadata, data, id representation of a leaf module fetcher.
    :param usage_key: A UsageKey
    """
    store = get_modulestore(usage_key)
    try:
        module = store.get_item(usage_key)
    except ItemNotFoundError:
        if usage_key.category in CREATE_IF_NOT_FOUND:
            # Create a new one for certain categories only. Used for course info handouts.
            store.create_and_save_xmodule(usage_key)
            module = store.get_item(usage_key)
        else:
            raise

    data = getattr(module, 'data', '')
    if rewrite_static_links:
        data = replace_static_urls(
            data,
            None,
            course_id=usage_key.course_key
        )

    # Note that children aren't being returned until we have a use case.
    return create_xblock_info(usage_key, module, data, own_metadata(module))
    # return {
    #     'id': unicode(usage_key),
    #     'data': data,
    #     'metadata': own_metadata(module)
    # }


def create_xblock_info(usage_key, xblock, data=None, metadata=None):
    """
    Creates the information needed for client-side XBlockInfo.

    If data or metadata are not specified, their information will not be added
    (regardless of whether or not the xblock actually has data or metadata).
    """
    publish_state = compute_publish_state(xblock) if xblock else None

    xblock_info = {
        "id": str(usage_key),
        "display_name": xblock.display_name_with_default,
        "category": xblock.category,
        "has_changes": get_modulestore(usage_key).has_changes(usage_key),
        "published": publish_state in (PublishState.public, PublishState.draft),
        "edited_on": get_default_time_display(xblock.edited_on) if xblock.edited_on else None,
        "edited_by": User.objects.get(id=xblock.edited_by).username if xblock.edited_by else None
    }
    if data is not None:
        xblock_info["data"] = data
    if metadata is not None:
        xblock_info["metadata"] = metadata

    return xblock_info