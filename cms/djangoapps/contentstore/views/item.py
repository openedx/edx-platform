"""Views for items (modules)."""

import logging
from uuid import uuid4
from requests.packages.urllib3.util import parse_url

from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.decorators import login_required

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError

from util.json_request import expect_json, JsonResponse

from ..transcripts_utils import manage_video_subtitles_save

from ..utils import get_modulestore, get_course_for_item

from .access import has_access
from .helpers import _xmodule_recurse
from xmodule.x_module import XModuleDescriptor
from django.views.decorators.http import require_http_methods
from xmodule.modulestore.locator import BlockUsageLocator
from student.models import CourseEnrollment

__all__ = ['create_item', 'orphan', 'xblock_handler']

log = logging.getLogger(__name__)

# cdodge: these are categories which should not be parented, they are detached from the hierarchy
DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']


@require_http_methods(("DELETE", "PUT", "POST"))
@login_required
@expect_json
def xblock_handler(request, tag=None, course_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for xblock requests.

    DELETE
        json: delete this xblock instance from the course. Supports query parameters "recurse" to delete
        all children and "all_versions" to delete from all (mongo) versions.
    PUT or POST
        json: update the xblock instance (note that create is not yet supported). The json payload can contain
        these fields, all optional:
            :data: the new value for the data.
            :children: the ids (old-style) of children for this xblock.
            :metadata: new values for the metadata fields. Any whose values are None will be deleted not set
                       to None! Absent ones will be left alone.
            :nullout: which metadata fields to set to None
    """
    location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    if not has_access(request.user, location):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(location)

    if request.method == 'DELETE':
        delete_children = bool(request.REQUEST.get('recurse', False))
        delete_all_versions = bool(request.REQUEST.get('all_versions', False))

        return _delete_item_at_location(old_location, delete_children, delete_all_versions)
    else:  # PUT or POST currently mapped to save.
        return _save_item(
            old_location,
            data=request.json.get('data'),
            children=request.json.get('children'),
            metadata=request.json.get('metadata'),
            nullout=request.json.get('nullout')
        )


def _save_item(item_location, data=None, children=None, metadata=None, nullout=None):
    """
    Saves certain properties (data, children, metadata, nullout) for a given xblock item.

    The item_location is still the old-style location.
    """
    store = get_modulestore(item_location)

    try:
        old_item = store.get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        return JsonResponse({"error": "Can't find item by location"}, 404)

    if data:
        store.update_item(item_location, data)

    if children is not None:
        store.update_children(item_location, children)

    # cdodge: also commit any metadata which might have been passed along
    if nullout is not None or metadata is not None:
        # the postback is not the complete metadata, as there's system metadata which is
        # not presented to the end-user for editing. So let's fetch the original and
        # 'apply' the submitted metadata, so we don't end up deleting system metadata
        existing_item = modulestore().get_item(item_location)
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

                if existing_item.category == 'video':

                    allowedSchemes = ['https']
                    # The entire site is served from https, so browsers with good
                    # security will reject non-https URLs anyway.
                    # Also, following video module specific code is here, because front-end
                    # metadata fields doesn't support validation.
                    if metadata_key == 'html5_sources' and not all([parse_url(u).scheme.lower() in allowedSchemes for u in value]):
                        raise ValidationError(u'HTML5 video sources support following protocols: {0}.'.format(' '.join(allowedSchemes)))
        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        existing_item.save()
        # commit to datastore
        store.update_metadata(item_location, own_metadata(existing_item))

        if existing_item.category == 'video':
            manage_video_subtitles_save(old_item, existing_item)

    return JsonResponse()


@login_required
@expect_json
def create_item(request):
    """View for create items."""
    parent_location = Location(request.json['parent_location'])
    category = request.json['category']

    display_name = request.json.get('display_name')

    if not has_access(request.user, parent_location):
        raise PermissionDenied()

    parent = get_modulestore(category).get_item(parent_location)
    dest_location = parent_location.replace(category=category, name=uuid4().hex)

    # get the metadata, display_name, and definition from the request
    metadata = {}
    data = None
    template_id = request.json.get('boilerplate')
    if template_id is not None:
        clz = XModuleDescriptor.load_class(category)
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
        system=parent.system,
    )

    if category not in DETACHED_CATEGORIES:
        get_modulestore(parent.location).update_children(parent_location, parent.children + [dest_location.url()])

    locator = loc_mapper().translate_location(
        get_course_for_item(parent_location).location.course_id, dest_location, False, True
    )
    return JsonResponse({'id': dest_location.url(), "update_url": locator.url_reverse("xblock")})


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
def orphan(request, tag=None, course_id=None, branch=None, version_guid=None, block=None):
    """
    View for handling orphan related requests. GET gets all of the current orphans.
    DELETE removes all orphans (requires is_staff access)

    An orphan is a block whose category is not in the DETACHED_CATEGORY list, is not the root, and is not reachable
    from the root via children

    :param request:
    :param course_id: Locator syntax course_id
    """
    location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    # DHM: when split becomes back-end, move or conditionalize this conversion
    old_location = loc_mapper().translate_locator_to_location(location)
    if request.method == 'GET':
        if has_access(request.user, old_location):
            return JsonResponse(modulestore().get_orphans(old_location, DETACHED_CATEGORIES, 'draft'))
        else:
            raise PermissionDenied()
    if request.method == 'DELETE':
        if request.user.is_staff:
            items = modulestore().get_orphans(old_location, DETACHED_CATEGORIES, 'draft')
            for item in items:
                modulestore('draft').delete_item(item, True)
            return JsonResponse({'deleted': items})
        else:
            raise PermissionDenied()
