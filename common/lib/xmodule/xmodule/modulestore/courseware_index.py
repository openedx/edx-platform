""" Code to allow module store to interface with courseware index """
from __future__ import absolute_import

import logging

from opaque_keys.edx.locator import CourseLocator
from search.search_engine_base import SearchEngine

from . import ModuleStoreEnum
from .exceptions import ItemNotFoundError

# Use default index and document names for now
INDEX_NAME = "courseware_index"
DOCUMENT_TYPE = "courseware_content"

log = logging.getLogger('edx.modulestore')


class IndexWriteError(Exception):

    """ Raised to indicate that indexing of particular key failed """
    pass


class ModuleStoreCoursewareIndexMixin(object):

    """
    Mixin class to enable indexing for courseware search from different modulestores
    """

    def do_index(self, location, delete=False):
        """
        Main routine to index (for purposes of searching) from given location and other stuff on down
        """
        error = []
        # TODO - inline for now, need to move this out to a celery task
        searcher = SearchEngine.get_search_engine(INDEX_NAME)
        if not searcher:
            return

        course_key = location if isinstance(location, CourseLocator) else location.course_key
        location_info = {
            "course": unicode(course_key),
        }

        def _fetch_item(item_location):
            """ Fetch the item from the modulestore location, log if not found, but continue """
            try:
                if isinstance(item_location, CourseLocator):
                    item = self.get_course(item_location)
                else:
                    item = self.get_item(item_location, revision=ModuleStoreEnum.RevisionOption.published_only)
            except ItemNotFoundError:
                log.warning('Cannot find: %s', item_location)
                return None

            return item

        def index_item_location(item_location, current_start_date):
            """ add this item to the search index """
            item = _fetch_item(item_location)
            if item:
                if item.category in ['course', 'chapter', 'sequential', 'vertical', 'html', 'video']:
                    if item.start and (not current_start_date or item.start > current_start_date):
                        current_start_date = item.start

                    if item.has_children:
                        for child_loc in item.children:
                            index_item_location(child_loc, current_start_date)

                    item_index = {}
                    try:
                        item_index.update(location_info)
                        item_index.update(item.index_dictionary())
                        item_index.update({
                            'id': unicode(item.scope_ids.usage_id),
                        })

                        if current_start_date:
                            item_index.update({
                                "start_date": current_start_date
                            })

                        searcher.index(DOCUMENT_TYPE, item_index)
                    except IndexWriteError:
                        log.warning('Could not index item: %s', item_location)
                        error.append('Could not index item: {}'.format(item_location))

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
                location.course_key,
                str(err)
            )

        return error

    def do_course_reindex(self, course_key):
        """
        Get the course with the given courseid (org/course/run)
        """
        return self.do_index(course_key, delete=False)
