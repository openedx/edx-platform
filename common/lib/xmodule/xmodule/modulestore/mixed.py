"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

IMPORTANT: This modulestore is experimental AND INCOMPLETE. Therefore this should only be used cautiously
"""

from . import ModuleStoreBase
from django import create_modulestore_instance


class MixedModuleStore(ModuleStoreBase):
    """
    ModuleStore that can be backed by either XML or Mongo
    """
    def __init__(self, mappings, stores):
        """
        Initialize a MixedModuleStore. Here we look into our passed in kwargs which should be a
        collection of other modulestore configuration informations
        """
        super(MixedModuleStore, self).__init__()

        self.modulestores = {}
        self.mappings = mappings
        for key in stores:
            self.modulestores[key] = create_modulestore_instance(stores[key]['ENGINE'],
                                                                 stores[key]['OPTIONS'])

    def _get_modulestore_for_courseid(self, course_id):
        """
        For a given course_id, look in the mapping table and see if it has been pinned
        to a particular modulestore
        """
        return self.mappings.get(course_id, self.mappings['default'])

    def has_item(self, course_id, location):
        return self._get_modulestore_for_courseid(course_id).has_item(course_id, location)

    def get_item(self, location, depth=0):
        """
        This method is explicitly not implemented as we need a course_id to disambiguate
        We should be able to fix this when the data-model rearchitecting is done
        """
        raise NotImplementedError

    def get_instance(self, course_id, location, depth=0):
        return self._get_modulestore_for_courseid(course_id).get_instance(course_id, location, depth)

    def get_items(self, location, course_id=None, depth=0):
        """
        Returns a list of XModuleDescriptor instances for the items
        that match location. Any element of location that is None is treated
        as a wildcard that matches any value

        location: Something that can be passed to Location

        depth: An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """
        if not course_id:
            raise Exception("Must pass in a course_id when calling get_items() with MixedModuleStore")

        return self._get_modulestore_for_courseid(course_id).get_items(location, course_id, depth)

    def update_item(self, location, data, allow_not_found=False):
        """
        MixedModuleStore is for read-only (aka LMS)
        """
        raise NotImplementedError

    def update_children(self, location, children):
        """
        MixedModuleStore is for read-only (aka LMS)
        """
        raise NotImplementedError

    def update_metadata(self, location, metadata):
        """
        MixedModuleStore is for read-only (aka LMS)
        """
        raise NotImplementedError

    def delete_item(self, location):
        """
        MixedModuleStore is for read-only (aka LMS)
        """
        raise NotImplementedError

    def get_courses(self):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.
        '''
        courses = []
        for key in self.modulestores:
            courses.append(self.modulestores[key].get_courses)
        return courses

    def get_course(self, course_id):
        """
        returns the course module associated with the course_id
        """
        return self._get_modulestore_for_courseid(course_id).get_course(course_id)

    def get_parent_locations(self, location, course_id):
        """
        returns the parent locations for a given lcoation and course_id
        """
        return self._get_modulestore_for_courseid(course_id).get_parent_locations(location, course_id)

    def set_modulestore_configuration(self, config_dict):
        """
        This implementation of the interface method will pass along the configuration to all ModuleStore
        instances
        """
        for store in self.modulestores.values():
            store.set_modulestore_configuration(config_dict)
