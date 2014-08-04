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
from xmodule_modifiers import wrap_xblock

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from xblock.fields import Scope
from xblock.fragment import Fragment

import xmodule
from xmodule.tabs import StaticTab, CourseTabList
from xmodule.modulestore import ModuleStoreEnum, PublishState
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.inheritance import own_metadata
from xmodule.x_module import PREVIEW_VIEWS, STUDIO_VIEW, STUDENT_VIEW

from xmodule.course_module import DEFAULT_START_DATE
from contentstore.utils import find_release_date_source
from django.contrib.auth.models import User
from util.date_utils import get_default_time_display

from util.json_request import expect_json, JsonResponse

from .access import has_course_access
from contentstore.utils import is_currently_visible_to_students
from contentstore.views.helpers import is_unit, xblock_studio_url, xblock_primary_child_category, \
    xblock_type_display_name, get_parent_xblock
from contentstore.views.preview import get_preview_fragment
from edxmako.shortcuts import render_to_string
from models.settings.course_grading import CourseGradingModel
from cms.lib.xblock.runtime import handler_url, local_resource_url
from opaque_keys.edx.keys import UsageKey, CourseKey

__all__ = ['orphan_handler', 'xblock_handler', 'xblock_view_handler', 'xblock_outline_handler']

log = logging.getLogger(__name__)

CREATE_IF_NOT_FOUND = ['course_info']

# Useful constants for defining predicates
NEVER = lambda x: False
ALWAYS = lambda x: True


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


def usage_key_with_run(usage_key_string):
    """
    Converts usage_key_string to a UsageKey, adding a course run if necessary
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    return usage_key


# pylint: disable=unused-argument
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
                rsp = _get_module_info(_get_xblock(usage_key, request.user))
                return JsonResponse(rsp)
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
                children=request.json.get('children'),
                metadata=request.json.get('metadata'),
                nullout=request.json.get('nullout'),
                grader_type=request.json.get('graderType'),
                publish=request.json.get('publish'),
            )
    elif request.method in ('PUT', 'POST'):
        if 'duplicate_source_locator' in request.json:
            parent_usage_key = usage_key_with_run(request.json['parent_locator'])
            duplicate_source_usage_key = usage_key_with_run(request.json['duplicate_source_locator'])

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
    usage_key = usage_key_with_run(usage_key_string)
    if not has_course_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

    if 'application/json' in accept_header:
        store = modulestore()
        xblock = store.get_item(usage_key)
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

            store.update_item(xblock, request.user.id)
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


# pylint: disable=unused-argument
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
    if not has_course_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        store = modulestore()
        root_xblock = store.get_item(usage_key)
        return JsonResponse(create_xblock_info(
            root_xblock,
            include_child_info=True,
            course_outline=True,
            include_children_predicate=lambda xblock: not xblock.category == 'vertical'
        ))
    else:
        return Http404


def _save_xblock(user, xblock, data=None, children=None, metadata=None, nullout=None,
                 grader_type=None, publish=None):
    """
    Saves xblock w/ its fields. Has special processing for grader_type, publish, and nullout and Nones in metadata.
    nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
    to default).
    """
    store = modulestore()

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

    if children is not None:
        children_usage_keys = []
        for child in children:
            child_usage_key = usage_key_with_run(child)
            children_usage_keys.append(child_usage_key)
        xblock.children = children_usage_keys

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
                    except ValueError:
                        return JsonResponse({"error": "Invalid data"}, 400)
                    field.write_to(xblock, value)

    if callable(getattr(xblock, "editor_saved", None)):
        xblock.editor_saved(user, old_metadata, old_content)

    # commit to datastore
    store.update_item(xblock, user.id)

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

    # If publish is set to 'republish' and this item has previously been published, then this
    # new item should be republished. This is used by staff locking to ensure that changing the draft
    # value of the staff lock will also update the published version.
    if publish == 'republish':
        published = modulestore().compute_publish_state(xblock) != PublishState.private
        if published:
            publish = 'make_public'

    # Make public after updating the xblock, in case the caller asked for both an update and a publish.
    # Used by Bok Choy tests and by republishing of staff locks.
    if publish == 'make_public':
        modulestore().publish(xblock.location, user.id)

    # Note that children aren't being returned until we have a use case.
    return JsonResponse(result)


@login_required
@expect_json
def _create_item(request):
    """View for create items."""
    usage_key = usage_key_with_run(request.json['parent_locator'])
    category = request.json['category']

    display_name = request.json.get('display_name')

    if not has_course_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    store = modulestore()
    parent = store.get_item(usage_key)
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

    # TODO need to fix components that are sending definition_data as strings, instead of as dicts
    # For now, migrate them into dicts here.
    if isinstance(data, basestring):
        data = {'data': data}

    created_block = store.create_child(
        request.user.id,
        usage_key,
        dest_usage_key.block_type,
        block_id=dest_usage_key.block_id,
        definition_data=data,
        metadata=metadata,
        runtime=parent.runtime,
    )

    # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
    # if we add one then we need to also add it to the policy information (i.e. metadata)
    # we should remove this once we can break this reference from the course to static tabs
    if category == 'static_tab':
        display_name = display_name or _("Empty") # Prevent name being None
        course = store.get_course(dest_usage_key.course_key)
        course.tabs.append(
            StaticTab(
                name=display_name,
                url_slug=dest_usage_key.name,
            )
        )
        store.update_item(course, request.user.id)

    return JsonResponse({"locator": unicode(created_block.location), "courseKey": unicode(created_block.location.course_key)})


def _duplicate_item(parent_usage_key, duplicate_source_usage_key, user, display_name=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_usage_key.
    """
    store = modulestore()
    source_item = store.get_item(duplicate_source_usage_key)
    # Change the blockID to be unique.
    dest_usage_key = source_item.location.replace(name=uuid4().hex)
    category = dest_usage_key.block_type

    # Update the display name to indicate this is a duplicate (unless display name provided).
    duplicate_metadata = own_metadata(source_item)
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

    # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
    # Because DAGs are not fully supported, we need to actually duplicate each child as well.
    if source_item.has_children:
        dest_module.children = []
        for child in source_item.children:
            dupe = _duplicate_item(dest_module.location, child, user=user)
            dest_module.children.append(dupe)
        store.update_item(dest_module, user.id)

    if not 'detached' in source_item.runtime.load_block_type(category)._class_tags:
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


def _delete_item(usage_key, user):
    """
    Deletes an existing xblock with the given usage_key.
    If the xblock is a Static Tab, removes it from course.tabs as well.
    """
    store = modulestore()

    # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
    # if we add one then we need to also add it to the policy information (i.e. metadata)
    # we should remove this once we can break this reference from the course to static tabs
    if usage_key.category == 'static_tab':
        course = store.get_course(usage_key.course_key)
        existing_tabs = course.tabs or []
        course.tabs = [tab for tab in existing_tabs if tab.get('url_slug') != usage_key.name]
        store.update_item(course, user.id)

    store.delete_item(usage_key, user.id)


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
            return JsonResponse([unicode(item) for item in modulestore().get_orphans(course_usage_key)])
        else:
            raise PermissionDenied()
    if request.method == 'DELETE':
        if request.user.is_staff:
            store = modulestore()
            items = store.get_orphans(course_usage_key)
            for itemloc in items:
                # need to delete all versions
                store.delete_item(itemloc, request.user.id, revision=ModuleStoreEnum.RevisionOption.all)
            return JsonResponse({'deleted': [unicode(item) for item in items]})
        else:
            raise PermissionDenied()


def _get_xblock(usage_key, user):
    """
    Returns the xblock for the specified usage key. Note: if failing to find a key with a category
    in the CREATE_IF_NOT_FOUND list, an xblock will be created and saved automatically.
    """
    store = modulestore()
    try:
        return store.get_item(usage_key)
    except ItemNotFoundError:
        if usage_key.category in CREATE_IF_NOT_FOUND:
            # Create a new one for certain categories only. Used for course info handouts.
            return store.create_item(user.id, usage_key.course_key, usage_key.block_type, block_id=usage_key.block_id)
        else:
            raise
    except InvalidLocationError:
        log.error("Can't find item by location.")
        return JsonResponse({"error": "Can't find item by location: " + unicode(usage_key)}, 404)


def _get_module_info(xblock, rewrite_static_links=True):
    """
    metadata, data, id representation of a leaf module fetcher.
    :param usage_key: A UsageKey
    """
    data = getattr(xblock, 'data', '')
    if rewrite_static_links:
        data = replace_static_urls(
            data,
            None,
            course_id=xblock.location.course_key
        )

    # Note that children aren't being returned until we have a use case.
    return create_xblock_info(xblock, data=data, metadata=own_metadata(xblock), include_ancestor_info=True)


def create_xblock_info(xblock, data=None, metadata=None, include_ancestor_info=False, include_child_info=False,
                       course_outline=False, include_children_predicate=NEVER, parent_xblock=None, graders=None):
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

    is_xblock_unit = is_unit(xblock, parent_xblock)
    is_unit_with_changes = is_xblock_unit and modulestore().has_changes(xblock)

    if graders is None:
        graders = CourseGradingModel.fetch(xblock.location.course_key).graders

    # Compute the child info first so it can be included in aggregate information for the parent
    should_visit_children = include_child_info and (course_outline and not is_xblock_unit or not course_outline)
    if should_visit_children and xblock.has_children:
        child_info = _create_xblock_child_info(
            xblock,
            course_outline,
            graders,
            include_children_predicate=include_children_predicate,
        )
    else:
        child_info = None

    # Treat DEFAULT_START_DATE as a magic number that means the release date has not been set
    release_date = get_default_time_display(xblock.start) if xblock.start != DEFAULT_START_DATE else None
    published = modulestore().compute_publish_state(xblock) != PublishState.private

    xblock_info = {
        "id": unicode(xblock.location),
        "display_name": xblock.display_name_with_default,
        "category": xblock.category,
        "edited_on": get_default_time_display(xblock.subtree_edited_on) if xblock.subtree_edited_on else None,
        "published": published,
        "published_on": get_default_time_display(xblock.published_date) if xblock.published_date else None,
        'studio_url': xblock_studio_url(xblock, parent_xblock),
        "released_to_students": datetime.now(UTC) > xblock.start,
        "release_date": release_date,
        "visibility_state": _compute_visibility_state(xblock, child_info, is_unit_with_changes) if not xblock.category == 'course' else None,
        "start": xblock.fields['start'].to_json(xblock.start),
        "graded": xblock.graded,
        "due_date": get_default_time_display(xblock.due),
        "due": xblock.fields['due'].to_json(xblock.due),
        "format": xblock.format,
        "course_graders": json.dumps([grader.get('type') for grader in graders]),
    }
    if data is not None:
        xblock_info["data"] = data
    if metadata is not None:
        xblock_info["metadata"] = metadata
    if include_ancestor_info:
        xblock_info['ancestor_info'] = _create_xblock_ancestor_info(xblock, course_outline)
    if child_info:
        xblock_info['child_info'] = child_info
    # Currently, 'edited_by', 'published_by', and 'release_date_from', and 'has_changes' are only used by the
    # container page when rendering a unit. Since they are expensive to compute, only include them for units
    # that are not being rendered on the course outline.
    if is_xblock_unit and not course_outline:
        xblock_info["edited_by"] = safe_get_username(xblock.subtree_edited_by)
        xblock_info["published_by"] = safe_get_username(xblock.published_by)
        xblock_info["currently_visible_to_students"] = is_currently_visible_to_students(xblock)
        xblock_info['has_changes'] = is_unit_with_changes
        if release_date:
            xblock_info["release_date_from"] = _get_release_date_from(xblock)

    return xblock_info


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
    children = child_info and child_info['children']
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


def _create_xblock_child_info(xblock, course_outline, graders, include_children_predicate=NEVER):
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
                graders=graders
            ) for child in xblock.get_children()
        ]
    return child_info


def _get_release_date_from(xblock):
    """
    Returns a string representation of the section or subsection that sets the xblock's release date
    """
    source = find_release_date_source(xblock)
    # Translators: this will be a part of the release date message.
    # For example, 'Released: Jul 02, 2014 at 4:00 UTC with Section "Week 1"'
    return _('{section_or_subsection} "{display_name}"').format(
        section_or_subsection=xblock_type_display_name(source),
        display_name=source.display_name_with_default)
