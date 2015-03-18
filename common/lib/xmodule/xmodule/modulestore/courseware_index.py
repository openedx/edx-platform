""" Code to allow module store to interface with courseware index """
from __future__ import absolute_import

import logging

from django.utils.translation import ugettext as _
from opaque_keys.edx.locator import CourseLocator, LibraryLocator
from search.search_engine_base import SearchEngine
from eventtracking import tracker

from . import ModuleStoreEnum
from .exceptions import ItemNotFoundError


# Use default index and document names for now


log = logging.getLogger('edx.modulestore')


def get_indexer_for_location(locator):
    if isinstance(locator, CourseLocator):
        return CoursewareSearchIndexer
    elif isinstance(locator, LibraryLocator):
        return LibrarySearchIndexer
    return get_indexer_for_location(locator.course_key)


class SearchIndexingError(Exception):
    """ Indicates some error(s) occured during indexing """

    def __init__(self, message, error_list):
        super(SearchIndexingError, self).__init__(message)
        self.error_list = error_list


class SearchIndexerBase(object):
    """
    Base class to perform XBlock indexing from different modulestores
    """
    INDEX_NAME = None
    DOCUMENT_TYPE = None

    index_on_create = True
    index_on_update = True
    index_on_delete = True
    index_on_publish = True

    @classmethod
    def _get_structure_key(cls, location):
        """ Gets structure key from location """
        return location.course_key

    @classmethod
    def _get_location_info(cls, structure_key):
        """ Builds location info dictionary """
        return {"course": unicode(structure_key)}

    @classmethod
    def _fetch_item(cls, modulestore, item_location):
        """ Fetch the item from the modulestore location, log if not found, but continue """
        try:
            if isinstance(item_location, CourseLocator):
                item = modulestore.get_course(item_location)
            else:
                item = modulestore.get_item(item_location, revision=ModuleStoreEnum.RevisionOption.published_only)
        except ItemNotFoundError:
            log.warning('Cannot find: %s', item_location)
            return None

        return item

    @classmethod
    def _id_modifier(cls, usage_id):
        """ Modifies usage_id to submit to index """
        return usage_id
    
    @classmethod
    def _track_index_request(cls, event_name, indexed_count, location=None):
        """Track content index requests.

        Arguments:
            location (str): The ID of content to be indexed.
            event_name (str):  Name of the event to be logged.
        Returns:
            None

        """
        data = {
            "indexed_count": indexed_count,
            'category': cls.INDEX_NAME,
        }

        if location:
            data['location_id'] = location

        tracker.emit(
            event_name,
            data
        )

    @classmethod
    def add_to_search_index(cls, modulestore, location, delete=False, raise_on_error=False):
        """
        Add to courseware search index from given location and its children
        """
        error_list = []
        indexed_count = 0
        # TODO - inline for now, need to move this out to a celery task
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        if not searcher:
            return

        structure_key = cls._get_structure_key(location)
        location_info = cls._get_location_info(structure_key)

        def index_item_location(item_location, current_start_date):
            """ add this item to the search index """
            item = cls._fetch_item(modulestore, item_location)
            if not item:
                return

            is_indexable = hasattr(item, "index_dictionary")
            # if it's not indexable and it does not have children, then ignore
            if not is_indexable and not item.has_children:
                return

            # if it has a defined start, then apply it and to it's children
            if item.start and (not current_start_date or item.start > current_start_date):
                current_start_date = item.start

            if item.has_children:
                for child_loc in item.children:
                    index_item_location(child_loc, current_start_date)

            item_index = {}
            item_index_dictionary = item.index_dictionary() if is_indexable else None

            # if it has something to add to the index, then add it
            if item_index_dictionary:
                try:
                    item_index.update(location_info)
                    item_index.update(item_index_dictionary)
                    item_index['id'] = unicode(cls._id_modifier(item.scope_ids.usage_id))
                    if current_start_date:
                        item_index['start_date'] = current_start_date

                    searcher.index(cls.DOCUMENT_TYPE, item_index)
                except Exception as err:  # pylint: disable=broad-except
                    # broad exception so that index operation does not fail on one item of many
                    log.warning('Could not index item: %s - %s', item_location, unicode(err))
                    error_list.append(_('Could not index item: {}').format(item_location))

        def remove_index_item_location(item_location):
            """ remove this item from the search index """
            item = cls._fetch_item(modulestore, item_location)
            if item:
                if item.has_children:
                    for child_loc in item.children:
                        remove_index_item_location(child_loc)

            searcher.remove(cls.DOCUMENT_TYPE, unicode(cls._id_modifier(item.scope_ids.usage_id)))

        try:
            if delete:
                remove_index_item_location(location)
            else:
                index_item_location(location, None)
            indexed_count += 1
        except Exception as err:  # pylint: disable=broad-except
            # broad exception so that index operation does not prevent the rest of the application from working
            log.exception(
                "Indexing error encountered, courseware index may be out of date %s - %s",
                structure_key,
                unicode(err)
            )
            error_list.append(_('General indexing error occurred'))

        if raise_on_error and error_list:
            raise SearchIndexingError(_('Error(s) present during indexing'), error_list)
        
        return indexed_count


class CoursewareSearchIndexer(SearchIndexerBase):
    """
    Class to perform indexing for courseware search from different modulestores
    """
    INDEX_NAME = "courseware_index"
    DOCUMENT_TYPE = "courseware_content"

    index_on_create = False
    index_on_update = False

    @classmethod
    def _get_structure_key(cls, location):
        """ Gets structure key from location """
        if isinstance(location, CourseLocator):
            course_key = location
        else:
            course_key = location.course_key
        return course_key

    @classmethod
    def do_publish_index(cls, modulestore, location, delete=False, raise_on_error=False):
        """
        Add to courseware search index published section and children
        """
        indexed_count = cls.add_to_search_index(modulestore, location, delete, raise_on_error)
        cls._track_index_request('edx.course.index.published', indexed_count, str(location))
        return indexed_count

    @classmethod
    def do_course_reindex(cls, modulestore, course_key):
        """
        (Re)index all content within the given course
        """
        indexed_count = cls.add_to_search_index(modulestore, course_key, delete=False, raise_on_error=True)
        cls._track_index_request('edx.course.index.reindexed', indexed_count)
        return indexed_count


class LibrarySearchIndexer(SearchIndexerBase):
    """
    Class to perform indexing for courseware search from different modulestores
    """
    INDEX_NAME = "library_index"
    DOCUMENT_TYPE = "library_content"

    @classmethod
    def _get_structure_key(cls, location):
        """ Gets structure key from location """
        if isinstance(location, LibraryLocator):
            course_key = location
        else:
            course_key = location.course_key.replace(version_guid=None, branch=None)
        return course_key

    @classmethod
    def _get_location_info(cls, structure_key):
        """ Builds location info dictionary """
        return {"library": unicode(structure_key)}

    @classmethod
    def _id_modifier(cls, usage_id):
        """ Modifies usage_id to submit to index """
        id_agnostic_library_key = usage_id.library_key.replace(version_guid=None, branch=None)
        return usage_id.replace(library_key=id_agnostic_library_key)

    @classmethod
    def _fetch_item(cls, modulestore, item_location):
        """ Fetch the item from the modulestore location, log if not found, but continue """
        try:
            if isinstance(item_location, CourseLocator):
                item = modulestore.get_library(item_location)
            else:
                item = modulestore.get_item(item_location)
        except ItemNotFoundError:
            log.warning('Cannot find: %s', item_location)
            return None

        return item