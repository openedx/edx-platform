import json
from uuid import uuid4

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from util.json_request import expect_json
from ..utils import get_modulestore
from .access import has_access
from .requests import _xmodule_recurse

__all__ = ['save_item', 'clone_item', 'delete_item']

# cdodge: these are categories which should not be parented, they are detached from the hierarchy
DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']


@login_required
@expect_json
def save_item(request):
    item_location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    store = get_modulestore(Location(item_location))

    if request.POST.get('data') is not None:
        data = request.POST['data']
        store.update_item(item_location, data)

    # cdodge: note calling request.POST.get('children') will return None if children is an empty array
    # so it lead to a bug whereby the last component to be deleted in the UI was not actually
    # deleting the children object from the children collection
    if 'children' in request.POST and request.POST['children'] is not None:
        children = request.POST['children']
        store.update_children(item_location, children)

    # cdodge: also commit any metadata which might have been passed along in the
    # POST from the client, if it is there
    # NOTE, that the postback is not the complete metadata, as there's system metadata which is
    # not presented to the end-user for editing. So let's fetch the original and
    # 'apply' the submitted metadata, so we don't end up deleting system metadata
    if request.POST.get('metadata') is not None:
        posted_metadata = request.POST['metadata']
        # fetch original
        existing_item = modulestore().get_item(item_location)

        # update existing metadata with submitted metadata (which can be partial)
        # IMPORTANT NOTE: if the client passed pack 'null' (None) for a piece of metadata that means 'remove it'
        for metadata_key, value in posted_metadata.items():

            if posted_metadata[metadata_key] is None:
                # remove both from passed in collection as well as the collection read in from the modulestore
                if metadata_key in existing_item._model_data:
                    del existing_item._model_data[metadata_key]
                del posted_metadata[metadata_key]
            else:
                existing_item._model_data[metadata_key] = value

        # commit to datastore
        # TODO (cpennington): This really shouldn't have to do this much reaching in to get the metadata
        store.update_metadata(item_location, own_metadata(existing_item))

    return HttpResponse()


@login_required
@expect_json
def clone_item(request):
    parent_location = Location(request.POST['parent_location'])
    template = Location(request.POST['template'])

    display_name = request.POST.get('display_name')

    if not has_access(request.user, parent_location):
        raise PermissionDenied()

    parent = get_modulestore(template).get_item(parent_location)
    dest_location = parent_location._replace(category=template.category, name=uuid4().hex)

    new_item = get_modulestore(template).clone_item(template, dest_location)

    # replace the display name with an optional parameter passed in from the caller
    if display_name is not None:
        new_item.display_name = display_name

    get_modulestore(template).update_metadata(new_item.location.url(), own_metadata(new_item))

    if new_item.location.category not in DETACHED_CATEGORIES:
        get_modulestore(parent.location).update_children(parent_location, parent.children + [new_item.location.url()])

    return HttpResponse(json.dumps({'id': dest_location.url()}))


@login_required
@expect_json
def delete_item(request):
    item_location = request.POST['id']
    item_location = Location(item_location)

    # check permissions for this user within this course
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    # optional parameter to delete all children (default False)
    delete_children = request.POST.get('delete_children', False)
    delete_all_versions = request.POST.get('delete_all_versions', False)

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

    return HttpResponse()
