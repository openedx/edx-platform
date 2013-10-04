import logging
from uuid import uuid4

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from util.json_request import expect_json, JsonResponse
from ..utils import get_modulestore
from .access import has_access
from .requests import _xmodule_recurse
from xmodule.x_module import XModuleDescriptor

__all__ = ['save_item', 'create_item', 'delete_item']

# cdodge: these are categories which should not be parented, they are detached from the hierarchy
DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']

log = logging.getLogger(__name__)

@login_required
@expect_json
def save_item(request):
    """
    Will carry a json payload with these possible fields
    :id (required): the id
    :data (optional): the new value for the data
    :metadata (optional): new values for the metadata fields.
        Any whose values are None will be deleted not set to None! Absent ones will be left alone
    :nullout (optional): which metadata fields to set to None
    """
    # The nullout is a bit of a temporary copout until we can make module_edit.coffee and the metadata editors a
    # little smarter and able to pass something more akin to {unset: [field, field]}

    try:
        item_location = request.POST['id']
    except KeyError:
        import inspect

        log.exception(
            '''Request missing required attribute 'id'.
                Request info:
                %s
                Caller:
                Function %s in file %s
            ''',
            request.META,
            inspect.currentframe().f_back.f_code.co_name,
            inspect.currentframe().f_back.f_code.co_filename
        )
        return HttpResponseBadRequest()


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

    # cdodge: also commit any metadata which might have been passed along
    if request.POST.get('nullout') is not None or request.POST.get('metadata') is not None:
        # the postback is not the complete metadata, as there's system metadata which is
        # not presented to the end-user for editing. So let's fetch the original and
        # 'apply' the submitted metadata, so we don't end up deleting system metadata
        existing_item = modulestore().get_item(item_location)
        for metadata_key in request.POST.get('nullout', []):
            setattr(existing_item, metadata_key, None)

        # update existing metadata with submitted metadata (which can be partial)
        # IMPORTANT NOTE: if the client passed 'null' (None) for a piece of metadata that means 'remove it'. If
        # the intent is to make it None, use the nullout field
        for metadata_key, value in request.POST.get('metadata', {}).items():
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

    return JsonResponse()


@login_required
@expect_json
def create_item(request):
    parent_location = Location(request.POST['parent_location'])
    category = request.POST['category']

    display_name = request.POST.get('display_name')

    if not has_access(request.user, parent_location):
        raise PermissionDenied()

    parent = get_modulestore(category).get_item(parent_location)
    dest_location = parent_location.replace(category=category, name=uuid4().hex)

    # get the metadata, display_name, and definition from the request
    metadata = {}
    data = None
    template_id = request.POST.get('boilerplate')
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

    return JsonResponse({'id': dest_location.url()})


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

    return JsonResponse()
