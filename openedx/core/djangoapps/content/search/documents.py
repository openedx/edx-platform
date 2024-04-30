"""
Utilities related to indexing content for search
"""
from __future__ import annotations

import logging
from hashlib import blake2b

from django.utils.text import slugify
from opaque_keys.edx.keys import LearningContextKey, UsageKey

from openedx.core.djangoapps.content.search.models import SearchAccess
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
    type = "type"  # DocType.course_block or DocType.library_block (see below)
    block_id = "block_id"  # The block_id part of the usage key. Sometimes human-readable, sometimes a random hex ID
    display_name = "display_name"
    block_type = "block_type"
    context_key = "context_key"
    org = "org"
    access_id = "access_id"  # .models.SearchAccess.id
    # breadcrumbs: an array of {"display_name": "..."} entries. First one is the name of the course/library itself.
    # After that is the name of any parent Section/Subsection/Unit/etc.
    # It's a list of dictionaries because for now we just include the name of each but in future we may add their IDs.
    breadcrumbs = "breadcrumbs"
    # tags (dictionary)
    # See https://blog.meilisearch.com/nested-hierarchical-facets-guide/
    # and https://www.algolia.com/doc/api-reference/widgets/hierarchical-menu/js/
    # For details on the format of the hierarchical tag data.
    # We currently have a hard-coded limit of 4 levels of tags in the search index (level0..level3).
    tags = "tags"
    tags_taxonomy = "taxonomy"  # subfield of tags, i.e. tags.taxonomy
    tags_level0 = "level0"  # subfield of tags, i.e. tags.level0
    tags_level1 = "level1"
    tags_level2 = "level2"
    tags_level3 = "level3"
    # The "content" field is a dictionary of arbitrary data, depending on the block_type.
    # It comes from each XBlock's index_dictionary() method (if present) plus some processing.
    # Text (html) blocks have an "html_content" key in here, capa has "capa_content" and "problem_types", and so on.
    content = "content"

    # Note: new fields or values can be added at any time, but if they need to be indexed for filtering or keyword
    # search, the index configuration will need to be changed, which is only done as part of the 'reindex_studio'
    # command (changing those settings on an large active index is not recommended).


class DocType:
    """
    Values for the 'type' field on each doc in the search index
    """
    course_block = "course_block"
    library_block = "library_block"


def meili_id_from_opaque_key(usage_key: UsageKey) -> str:
    """
    Meilisearch requires each document to have a primary key that's either an
    integer or a string composed of alphanumeric characters (a-z A-Z 0-9),
    hyphens (-) and underscores (_). Since our opaque keys don't meet this
    requirement, we transform them to a similar slug ID string that does.

    In the future, with Learning Core's data models in place for courseware,
    we could use PublishableEntity's primary key / UUID instead.
    """
    # The slugified key _may_ not be unique so we append a hashed string to make it unique:
    key_bin = str(usage_key).encode()
    suffix = blake2b(key_bin, digest_size=4).hexdigest()  # When we use Python 3.9+, should add usedforsecurity=False
    return slugify(str(usage_key)) + "-" + suffix


def _meili_access_id_from_context_key(context_key: LearningContextKey) -> int:
    """
    Retrieve the numeric access id for the given course/library context.
    """
    access, _ = SearchAccess.objects.get_or_create(context_key=context_key)
    return access.id


def _fields_from_block(block) -> dict:
    """
    Given an XBlock instance, call its index_dictionary() method to load any
    data that it wants included in the search index. Format into a flat dict.

    Note: the format of index_dictionary() depends on the block type. The base
    class implementation returns only:
        {"content": {"display_name": "..."}, "content_type": "..."}
    """
    block_data = {
        Fields.usage_key: str(block.usage_key),
        Fields.block_id: str(block.usage_key.block_id),
        Fields.display_name: xblock_api.get_block_display_name(block),
        Fields.block_type: block.scope_ids.block_type,
        # This is called context_key so it's the same for courses and libraries
        Fields.context_key: str(block.usage_key.context_key),  # same as lib_key
        Fields.org: str(block.usage_key.context_key.org),
        Fields.access_id: _meili_access_id_from_context_key(block.usage_key.context_key),
        Fields.breadcrumbs: []
    }
    # Get the breadcrumbs (course, section, subsection, etc.):
    if block.usage_key.context_key.is_course:  # Getting parent is not yet implemented in Learning Core (for libraries).
        cur_block = block
        while cur_block.parent:
            if not cur_block.has_cached_parent:
                # This is not a big deal, but if you're updating many blocks in the same course at once,
                # this would be very inefficient. Better to recurse the tree top-down with the parent blocks loaded.
                log.warning(f"Updating Studio search index for XBlock {block.usage_key} but ancestors weren't cached.")
            cur_block = cur_block.get_parent()
            parent_data = {
                "display_name": xblock_api.get_block_display_name(cur_block),
            }
            if cur_block.scope_ids.block_type != "course":
                parent_data["usage_key"] = str(cur_block.usage_key)
            block_data[Fields.breadcrumbs].insert(
                0,
                parent_data,
            )
    try:
        content_data = block.index_dictionary()
        # Will be something like:
        # {
        #     'content': {'display_name': '...', 'capa_content': '...'},
        #     'content_type': 'CAPA',
        #     'problem_types': ['multiplechoiceresponse']
        # }
        # Which we need to flatten:
        if "content_type" in content_data:
            del content_data["content_type"]  # Redundant with our standard Fields.block_type field.
        if "content" in content_data and isinstance(content_data["content"], dict):
            content = content_data["content"]
            if "display_name" in content:
                del content["display_name"]
            del content_data["content"]
            content_data.update(content)
        # Now we have something like:
        # { 'capa_content': '...', 'problem_types': ['multiplechoiceresponse'] }
        block_data[Fields.content] = content_data
    except Exception as err:  # pylint: disable=broad-except
        log.exception(f"Failed to process index_dictionary for {block.usage_key}: {err}")
    return block_data


def _tags_for_content_object(object_id: UsageKey | LearningContextKey) -> dict:
    """
    Given an XBlock, course, library, etc., get the tag data for its index doc.

    See the comments above on "Field.tags" for an explanation of the format.

    e.g. for something tagged "Difficulty: Hard" and "Location: Vancouver" this
    would return:
        {
            "tags": {
                "taxonomy": ["Location", "Difficulty"],
                "level0": ["Location > North America", "Difficulty > Hard"],
                "level1": ["Location > North America > Canada"],
                "level2": ["Location > North America > Canada > Vancouver"],
            }
        }

    Note: despite what you might expect, because this is only used for the
    filtering/refinement UI, it's fine if this is a one-way transformation.
    It's not necessary to be able to re-construct the exact tag IDs nor taxonomy
    IDs from this data that's stored in the search index. It's just a bunch of
    strings in a particular format that the frontend knows how to render to
    support hierarchical refinement by tag.
    """
    # Note that we could improve performance for indexing many components from the same library/course,
    # if we used get_all_object_tags() to load all the tags for the library in a single query rather than loading the
    # tags for each component separately.
    all_tags = tagging_api.get_object_tags(str(object_id)).all()
    if not all_tags:
        # Clear out tags in the index when unselecting all tags for the block, otherwise
        # it would remain the last value if a cleared Fields.tags field is not included
        return {Fields.tags: {}}
    result = {
        Fields.tags_taxonomy: [],
        Fields.tags_level0: [],
        # ... other levels added as needed
    }
    for obj_tag in all_tags:
        # Add the taxonomy name:
        if obj_tag.taxonomy.name not in result[Fields.tags_taxonomy]:
            result[Fields.tags_taxonomy].append(obj_tag.taxonomy.name)
        # Taxonomy name plus each level of tags, in a list: # e.g. ["Location", "North America", "Canada", "Vancouver"]
        parts = [obj_tag.taxonomy.name] + obj_tag.get_lineage()
        parts = [part.replace(" > ", " _ ") for part in parts]  # Escape our separator.
        # Now we build each level (tags.level0, tags.level1, etc.) as applicable.
        # We have a hard-coded limit of 4 levels of tags for now (see Fields.tags above).
        # A tag like "Difficulty: Hard" will only result in one level (tags.level0)
        # But a tag like "Location: North America > Canada > Vancouver" would result in three levels (tags.level0:
        #   "North America", tags.level1: "North America > Canada", tags.level2: "North America > Canada > Vancouver")
        # See the comments above on "Field.tags" for an explanation of why we use this format (basically it's the format
        # required by the Instantsearch frontend).
        for level in range(4):
            # We use '>' as a separator because it's the default for the Instantsearch frontend library, and our
            # preferred separator (\t) used in the database is ignored by Meilisearch since it's whitespace.
            new_value = " > ".join(parts[0:level + 2])
            if f"level{level}" not in result:
                result[f"level{level}"] = [new_value]
            elif new_value not in result[f"level{level}"]:
                result[f"level{level}"].append(new_value)
            if len(parts) == level + 2:
                break  # We have all the levels for this tag now (e.g. parts=["Difficulty", "Hard"] -> need level0 only)

    return {Fields.tags: result}


def searchable_doc_for_library_block(xblock_metadata: lib_api.LibraryXBlockMetadata) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, so that the given library block can be
    found using faceted search.
    """
    library_name = lib_api.get_library(xblock_metadata.usage_key.context_key).title
    block = xblock_api.load_block(xblock_metadata.usage_key, user=None)

    doc = {
        Fields.id: meili_id_from_opaque_key(xblock_metadata.usage_key),
        Fields.type: DocType.library_block,
        Fields.breadcrumbs: []
    }

    doc.update(_fields_from_block(block))

    # Add the breadcrumbs. In v2 libraries, the library itself is not a "parent" of the XBlocks so we add it here:
    doc[Fields.breadcrumbs] = [{"display_name": library_name}]

    return doc


def searchable_doc_tags(usage_key: UsageKey) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, with the tags data for the given content object.
    """
    doc = {
        Fields.id: meili_id_from_opaque_key(usage_key),
    }
    doc.update(_tags_for_content_object(usage_key))

    return doc


def searchable_doc_for_course_block(block) -> dict:
    """
    Generate a dictionary document suitable for ingestion into a search engine
    like Meilisearch or Elasticsearch, so that the given course block can be
    found using faceted search.
    """
    doc = {
        Fields.id: meili_id_from_opaque_key(block.usage_key),
        Fields.type: DocType.course_block,
    }

    doc.update(_fields_from_block(block))

    return doc
