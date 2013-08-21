from static_replace import replace_static_urls
from xmodule.modulestore.exceptions import ItemNotFoundError


def get_module_info(store, location, rewrite_static_links=False):
    try:
        module = store.get_item(location)
    except ItemNotFoundError:
        # create a new one
        store.create_and_save_xmodule(location)
        module = store.get_item(location)

    data = module.data
    if rewrite_static_links:
        # we pass a partially bogus course_id as we don't have the RUN information passed yet
        # through the CMS. Also the contentstore is also not RUN-aware at this point in time.
        data = replace_static_urls(
            module.data,
            None,
            course_id=module.location.org + '/' + module.location.course + '/BOGUS_RUN_REPLACE_WHEN_AVAILABLE'
        )

    return {
        'id': module.location.url(),
        'data': data,
        # TODO (cpennington): This really shouldn't have to do this much reaching in to get the metadata
        # what's the intent here? all metadata incl inherited & namespaced?
        'metadata': module.xblock_kvs._metadata
    }


def set_module_info(store, location, post_data):
    module = None
    try:
        module = store.get_item(location)
    except ItemNotFoundError:
        # new module at this location: almost always used for the course about pages; thus, no parent. (there
        # are quite a handful of about page types available for a course and only the overview is pre-created)
        store.create_and_save_xmodule(location)
        module = store.get_item(location)

    if post_data.get('data') is not None:
        data = post_data['data']
        store.update_item(location, data)

    # cdodge: note calling request.POST.get('children') will return None if children is an empty array
    # so it lead to a bug whereby the last component to be deleted in the UI was not actually
    # deleting the children object from the children collection
    if 'children' in post_data and post_data['children'] is not None:
        children = post_data['children']
        store.update_children(location, children)

    # cdodge: also commit any metadata which might have been passed along in the
    # POST from the client, if it is there
    # NOTE, that the postback is not the complete metadata, as there's system metadata which is
    # not presented to the end-user for editing. So let's fetch the original and
    # 'apply' the submitted metadata, so we don't end up deleting system metadata
    if post_data.get('metadata') is not None:
        posted_metadata = post_data['metadata']

        # update existing metadata with submitted metadata (which can be partial)
        # IMPORTANT NOTE: if the client passed pack 'null' (None) for a piece of metadata that means 'remove it'
        for metadata_key, value in posted_metadata.items():

            if posted_metadata[metadata_key] is None:
                # remove both from passed in collection as well as the collection read in from the modulestore
                if metadata_key in module._model_data:
                    del module._model_data[metadata_key]
                del posted_metadata[metadata_key]
            else:
                module._model_data[metadata_key] = value

        # commit to datastore
        # TODO (cpennington): This really shouldn't have to do this much reaching in to get the metadata
        store.update_metadata(location, module.xblock_kvs._metadata)
