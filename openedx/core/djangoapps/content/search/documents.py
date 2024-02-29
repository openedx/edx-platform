"""
Utilities related to searching content libraries
"""
import logging

from django.utils.text import slugify
from opaque_keys.edx.keys import UsageKey

from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.content_tagging import api as tagging_api
from openedx.core.djangoapps.xblock import api as xblock_api

log = logging.getLogger(__name__)


class Fields:
    """
    Fields that exist on the documents in our search index
    """
    # Meilisearch primary key. String.
    id = "id"
    usage_key = "usage_key"
    block_id = "block_id"
    display_name = "display_name"
    block_type = "block_type"
    context_key = "context_key"
    org = "org"
    # type: "course_block", "library_block"
    type = "type"


class DocType:
    """
    Values for the 'type' field on each doc in the search index
    """
    course_block = "course_block"
    library_block = "library_block"


def _meili_id_from_opaque_key(usage_key: UsageKey) -> str:
    """
    Meilisearch requires each document to have a primary key that's either an
    integer or a string composed of alphanumeric characters (a-z A-Z 0-9),
    hyphens (-) and underscores (_). Since our opaque keys don't meet this
    requirement, we transform them to a similar slug ID string that does.
    """
    # The slugified key _may_ not be unique so we append a hashed number too
    return slugify(str(usage_key)) + "-" + str(hash(str(usage_key)) % 1_000)


def _fields_from_block(block) -> dict:
    """
    Given an XBlock instance, call its index_dictionary() method to load any
    data that it wants included in the search index. Format into a flat dict.

    Note: the format of index_dictionary() depends on the block type. The base
    class implementation returns only:
        {"content": {"display_name": "..."}, "content_type": "..."}
    """
    try:
        block_data = block.index_dictionary()
        # Will be something like:
        # {
        #     'content': {'display_name': '...', 'capa_content': '...'},
        #     'content_type': 'CAPA',
        #     'problem_types': ['multiplechoiceresponse']
        # }
        # Which we need to flatten:
        if "content_type" in block_data:
            del block_data["content_type"]  # Redundant with our "type" field that we add later
        if "content" in block_data and isinstance(block_data["content"], dict):
            content = block_data["content"]
            if "display_name" in content:
                del content["display_name"]
            del block_data["content"]
            block_data.update(content)
        # Now we have something like:
        # { 'capa_content': '...', 'problem_types': ['multiplechoiceresponse'] }
    except Exception as err:  # pylint: disable=broad-except
        log.exception(f"Failed to process index_dictionary for {block.usage_key}: {err}")
        block_data = {}
    block_data.update({
        Fields.id: _meili_id_from_opaque_key(block.usage_key),
        Fields.usage_key: str(block.usage_key),
        Fields.block_id: str(block.usage_key.block_id),
        Fields.display_name: block.display_name,  # TODO: there is some function to get the fallback display_name
        Fields.block_type: block.scope_ids.block_type,
        # This is called context_key so it's the same for courses and libraries
        Fields.context_key: str(block.usage_key.context_key),  # same as lib_key
        Fields.org: str(block.usage_key.context_key.org),
    })
    return block_data


def searchable_doc_for_library_block(metadata: lib_api.LibraryXBlockMetadata) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, so that the given library block can be
    found using faceted search.
    """
    doc = {}
    try:
        block = xblock_api.load_block(metadata.usage_key, user=None)
    except Exception as err:  # pylint: disable=broad-except
        log.exception(f"Failed to load XBlock {metadata.usage_key}: {err}")
        # Even though we couldn't load the block, we can still include basic data about it in the index, from 'metadata'
        doc.update({
            Fields.id: _meili_id_from_opaque_key(metadata.usage_key),
            Fields.usage_key: str(metadata.usage_key),
            Fields.block_id: str(metadata.usage_key.block_id),
            Fields.display_name: metadata.display_name,
            Fields.type: metadata.usage_key.block_type,
            Fields.context_key: str(metadata.usage_key.context_key),
            Fields.org: str(metadata.usage_key.context_key.org),
        })
    else:
        doc.update(_fields_from_block(block))
    doc[Fields.type] = DocType.library_block
    # Add tags. Note that we could improve performance for indexing many components from the same library,
    # if we used get_all_object_tags() to load all the tags for the library in a single query rather than loading the
    # tags for each component separately.
    for obj_tag in tagging_api.get_object_tags(metadata.usage_key).all():
        key = f"tags:{obj_tag.name}"  # Taxonomy name
        if key not in doc:
            doc[key] = []
        # Add the tag and all its parent tags, which are implied
        for tag_value in obj_tag.get_lineage():
            if tag_value not in doc[key]:
                doc[key].append(tag_value)
    return doc


def searchable_doc_for_course_block(block) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, so that the given library block can be
    found using faceted search.
    """
    doc = _fields_from_block(block)
    doc[Fields.type] = DocType.course_block
    # Add tags. Note that we could improve performance for indexing many components from the same library,
    # if we used get_all_object_tags() to load all the tags for the library in a single query rather than loading the
    # tags for each component separately.
    for obj_tag in tagging_api.get_object_tags(block.usage_key).all():
        key = f"tags:{obj_tag.name}"  # Taxonomy name
        if key not in doc:
            doc[key] = []
        # Add the tag and all its parent tags, which are implied
        for tag_value in obj_tag.get_lineage():
            if tag_value not in doc[key]:
                doc[key].append(tag_value)
    return doc
