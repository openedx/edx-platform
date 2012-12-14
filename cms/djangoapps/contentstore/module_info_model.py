import logging

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from lxml import etree
import re
from django.http import HttpResponseBadRequest, Http404

def get_module_info(store, location, parent_location = None):
  try:
    if location.revision is None:
        module = store.get_item(location)
    else:
        module = store.get_item(location)
  except ItemNotFoundError:
    raise Http404

  return {
        'id': module.location.url(),
        'data': module.definition['data'],
        'metadata': module.metadata
    }

def set_module_info(store, location, post_data):
  module = None
  isNew = False
  try:
    if location.revision is None:
        module = store.get_item(location)
    else:
        module = store.get_item(location)
  except:
    pass

  if module is None:
    # new module at this location
    # presume that we have an 'Empty' template
    template_location = Location(['i4x', 'edx', 'templates', location.category, 'Empty'])
    module = store.clone_item(template_location, location)
    isNew = True

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
      for metadata_key in posted_metadata.keys():

          # let's strip out any metadata fields from the postback which have been identified as system metadata
          # and therefore should not be user-editable, so we should accept them back from the client
          if metadata_key in module.system_metadata_fields:
              del posted_metadata[metadata_key]
          elif posted_metadata[metadata_key] is None:
              # remove both from passed in collection as well as the collection read in from the modulestore
              if metadata_key in module.metadata:
                  del module.metadata[metadata_key]
              del posted_metadata[metadata_key]

      # overlay the new metadata over the modulestore sourced collection to support partial updates
      module.metadata.update(posted_metadata)

      # commit to datastore
      store.update_metadata(location, module.metadata)
