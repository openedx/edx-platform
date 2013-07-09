"""Views for items (modules)."""

import os
import json
import logging
from uuid import uuid4
from lxml import etree

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError

from util.json_request import expect_json
from ..utils import (get_modulestore, download_youtube_subs,
                     return_ajax_status, generate_subs_from_source,
                     generate_srt_from_sjson)
from .access import has_access
from .requests import _xmodule_recurse

__all__ = [
    'save_item', 'clone_item', 'delete_item', 'import_subtitles',
    'upload_subtitles', 'download_subtitles']

log = logging.getLogger(__name__)

# cdodge: these are categories which should not be parented, they are detached from the hierarchy
DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']


@login_required
@expect_json
def save_item(request):
    """View saving items."""
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
@return_ajax_status
def import_subtitles(request):
    """Try to import subtitles from Youtube for current modules."""

    # This view return True/False, cause we use `return_ajax_status`
    # view decorator.

    item_location = request.POST.get('id')
    if not item_location:
        log.error('POST data without "id" property.')
        return False

    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        return False

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'videoalpha':
        log.error('Subtitles are supported only for videoalpha" modules.')
        return False

    try:
        xmltree = etree.fromstring(item.data)
    except etree.XMLSyntaxError:
        log.error("Can't parse source XML.")
        return False

    youtube = xmltree.get('youtube')
    if not youtube:
        log.error('Missing or blank "youtube" attribute.')
        return False

    try:
        youtube_subs = dict([
            (float(i.split(':')[0]), i.split(':')[1])
            for i in youtube.split(',')
        ])
    except (IndexError, ValueError):
        # Get `IndexError` if after splitting by ':' we have one item
        # (missing ':' in the "youtube" attribute value).
        # Get `ValueError` when after splitting by ':' key can't convert
        # to float.
        log.error('Bad "youtube" attribute.')
        return False

    status = download_youtube_subs(youtube_subs, item)

    return status


@login_required
@return_ajax_status
def upload_subtitles(request):
    """Try to upload subtitles for current module."""

    # This view return True/False, cause we use `return_ajax_status`
    # view decorator.

    item_location = request.POST.get('id')
    if not item_location:
        log.error('POST data without "id" form data.')
        return False

    if 'file' not in request.FILES:
        log.error('POST data without "file" form data.')
        return False

    source_subs_filedata = request.FILES['file'].read()
    source_subs_filename = request.FILES['file'].name

    if '.' not in source_subs_filename:
        log.error("Undefined file extension.")
        return False

    basename = os.path.basename(source_subs_filename)
    source_subs_name = os.path.splitext(basename)[0]
    source_subs_ext = os.path.splitext(basename)[1][1:]

    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        return False

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'videoalpha':
        log.error('Subtitles are supported only for "videoalpha" modules.')
        return False

    try:
        xmltree = etree.fromstring(item.data)
    except etree.XMLSyntaxError:
        log.error("Can't parse source XML.")
        return False

    youtube_attr = xmltree.get('youtube')
    xml_sources = xmltree.findall('source')

    if youtube_attr:
        try:
            speed_subs = dict([
                (float(i.split(':')[0]), i.split(':')[1])
                for i in youtube_attr.split(',')
            ])
        except (IndexError, ValueError):
            # Get `IndexError` if after splitting by ':' we have one item
            # (missing ':' in the "youtube" attribute value).
            # Get `ValueError` when after splitting by ':' key can't convert
            # to float.
            log.error('Bad "youtube" attribute.')
            return False

        status = generate_subs_from_source(
            speed_subs,
            source_subs_ext,
            source_subs_filedata,
            item)

    elif xml_sources:
        sub_attr = slugify(source_subs_name)

        # Generate only one subs for speed = 1.0
        status = generate_subs_from_source(
            {1: sub_attr},
            source_subs_ext,
            source_subs_filedata,
            item)

        if status:
            xmltree.set('sub', sub_attr)
            store = get_modulestore(Location(item_location))
            store.update_item(item_location, etree.tostring(xmltree))
    else:
        log.error('Missing or blank "youtube" attribute and "source" tag.')
        return False

    return status, {'xml': etree.tostring(xmltree)}


@login_required
def download_subtitles(request):
    """Try to download subtitles for current modules."""

    # This view return True/False, cause we use `return_ajax_status`
    # view decorator.

    item_location = request.GET.get('id')
    if not item_location:
        log.error('GET data without "id" property.')
        raise Http404

    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        raise Http404

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'videoalpha':
        log.error('Subtitles are supported only for videoalpha" modules.')
        raise Http404

    try:
        xmltree = etree.fromstring(item.data)
    except etree.XMLSyntaxError:
        log.error("Can't parse source XML.")
        raise Http404

    youtube_attr = xmltree.get('youtube')
    sub_attr = xmltree.get('sub')

    speed = 1
    if youtube_attr:
        try:
            speed_subs = dict([
                (float(i.split(':')[0]), i.split(':')[1])
                for i in youtube_attr.split(',')
            ])
        except (IndexError, ValueError):
            # Get `IndexError` if after splitting by ':' we have one item
            # (missing ':' in the "youtube" attribute value).
            # Get `ValueError` when after splitting by ':' key can't convert
            # to float.
            log.error('Bad "youtube" attribute.')
            raise Http404

        # Iterate from highest to lowest speed and try to find available
        # subtitles in the store.
        sjson_subtitles = None
        youtube_id = None
        for speed, youtube_id in sorted(speed_subs.iteritems(), reverse=True):
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(
                item.location.org, item.location.course, filename)
            try:
                sjson_subtitles = contentstore().find(content_location)
                break
            except NotFoundError:
                continue

        if sjson_subtitles is None or youtube_id is None:
            log.error("Can't find content in storage for youtube IDs.")
            raise Http404

        srt_file_name = youtube_id

    elif sub_attr:
        filename = 'subs_{0}.srt.sjson'.format(sub_attr)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            sjson_subtitles = contentstore().find(content_location)
        except NotFoundError:
            log.error("Can't find content in storage for non-youtube sub.")
            raise Http404

        srt_file_name = sub_attr
    else:
        log.error('Missing or blank "youtube" attribute and "source" tag.')
        raise Http404

    str_subs = generate_srt_from_sjson(json.loads(sjson_subtitles.data), speed)
    if str_subs is None:
        raise Http404

    response = HttpResponse(str_subs, content_type='application/x-subrip')
    response['Content-Disposition'] = 'attachment; filename="{0}.srt"'.format(
        srt_file_name)

    return response


@login_required
@expect_json
def clone_item(request):
    """View for cloning items."""
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
    """View for removing items."""
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
