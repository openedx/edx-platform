import logging

from django.utils.text import slugify

from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.xblock import api as xblock_api

log = logging.getLogger(__name__)


def searchable_doc_for_library_block(metadata: lib_api.LibraryXBlockMetadata) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, so that the given library block can be
    found using faceted search.
    """
    doc = {}
    try:
        block = xblock_api.load_block(metadata.usage_key, user=None)
        block_data = block.index_dictionary()
        # Will be something like:
        # {
        #     'content': {'display_name': '...', 'capa_content': '...'},
        #     'content_type': 'CAPA',
        #     'problem_types': ['multiplechoiceresponse']
        # }
        # Which we need to flatten:
        if "content_type" in block_data:
            del block_data["content_type"]  # Redundant with our "type" field
        if "content" in block_data and isinstance(block_data["content"], dict):
            content = block_data["content"]
            if "display_name" in content:
                del content["display_name"]
            del block_data["content"]
            block_data.update(content)
        # Now we have
        # { 'capa_content': '...', 'problem_types': ['multiplechoiceresponse'] }
        doc.update(block_data)
    except Exception as err:
        log.exception(f"Failed to get index_dictionary for {metadata.usage_key}: {err}")
    # The data below must always override any values from index_dictionary:
    doc.update({
        # A Meilisearch document identifier can be of type integer or string,
        # only composed of alphanumeric characters (a-z A-Z 0-9), hyphens (-) and underscores (_).
        # So our usage keys with ":" characters cannot be used as primary keys.
        "id": slugify(str(metadata.usage_key)) + "-" + str(hash(str(metadata.usage_key)) % 1_000),
        "usage_key": str(metadata.usage_key),
        "block_id": str(metadata.usage_key.block_id),
        "display_name": metadata.display_name,
        "type": metadata.usage_key.block_type,
        # This is called contextKey not libKey so we can use the same keys with courses, and maybe search
        # both courses and libraries together in the future?
        "context_key": str(metadata.usage_key.context_key),  # same as lib_key
        "org": str(metadata.usage_key.context_key.org),
    })
    return doc
