""" Code to allow module store to interface with courseware index """
from __future__ import absolute_import

import logging

from django.utils.translation import ugettext as _
from opaque_keys.edx.locator import CourseLocator
from search.search_engine_base import SearchEngine

from . import ModuleStoreEnum
from .exceptions import ItemNotFoundError

# Use default index and document names for now
INDEX_NAME = "courseware_index"
DOCUMENT_TYPE = "courseware_content"

log = logging.getLogger('edx.modulestore')


class SearchIndexingError(Exception):
    """ Indicates some error(s) occured during indexing """

    def __init__(self, message, error_list):
        super(SearchIndexingError, self).__init__(message)
        self.error_list = error_list


class CoursewareSearchIndexer(object):
    """
    Class to perform indexing for courseware search from different modulestores
    """

    @staticmethod
    def add_to_search_index(modulestore, location, delete=False, raise_on_error=False):
        """
        Add to courseware search index from given location and its children
        """
        error_list = []
        # TODO - inline for now, need to move this out to a celery task
        searcher = SearchEngine.get_search_engine(INDEX_NAME)
        if not searcher:
            return

        if isinstance(location, CourseLocator):
            course_key = location
        else:
            course_key = location.course_key

        location_info = {
            "course": unicode(course_key),
        }

        def _fetch_item(item_location):
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

        def index_item_location(item_location, current_start_date):
            """ add this item to the search index """
            item = _fetch_item(item_location)
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
                    item_index['id'] = unicode(item.scope_ids.usage_id)
                    if current_start_date:
                        item_index['start_date'] = current_start_date

                    searcher.index(DOCUMENT_TYPE, item_index)
                except Exception as err:  # pylint: disable=broad-except
                    # broad exception so that index operation does not fail on one item of many
                    log.warning('Could not index item: %s - %s', item_location, unicode(err))
                    error_list.append(_('Could not index item: {}').format(item_location))

        def remove_index_item_location(item_location):
            """ remove this item from the search index """
            item = _fetch_item(item_location)
            if item:
                if item.has_children:
                    for child_loc in item.children:
                        remove_index_item_location(child_loc)

                searcher.remove(DOCUMENT_TYPE, unicode(item.scope_ids.usage_id))

        try:
            if delete:
                remove_index_item_location(location)
            else:
                index_item_location(location, None)
        except Exception as err:  # pylint: disable=broad-except
            # broad exception so that index operation does not prevent the rest of the application from working
            log.exception(
                "Indexing error encountered, courseware index may be out of date %s - %s",
                course_key,
                unicode(err)
            )
            error_list.append(_('General indexing error occurred'))

        if raise_on_error and error_list:
            raise SearchIndexingError(_('Error(s) present during indexing'), error_list)

    @classmethod
    def do_course_reindex(cls, modulestore, course_key):
        """
        (Re)index all content within the given course
        """
        return cls.add_to_search_index(modulestore, course_key, delete=False, raise_on_error=True)
