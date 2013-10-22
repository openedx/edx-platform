'''
Method for converting among our differing Location/Locator whatever reprs
'''
from random import randint
import re
import pymongo

from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, DuplicateItemError
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore.mongo import draft
from xmodule.modulestore import Location
import urllib


class LocMapperStore(object):
    '''
    This store persists mappings among the addressing schemes. At this time, it's between the old i4x Location
    tuples and the split mongo Course and Block Locator schemes.

    edX has used several different addressing schemes. The original ones were organically created based on
    immediate needs and were overly restrictive esp wrt course ids. These were slightly extended to support
    some types of blocks may need to have draft states during editing to keep live courses from seeing the wip.
    A later refactoring generalized course ids to enable governance and more complex naming, branch naming with
    anything able to be in any branch.

    The expectation is that the configuration will have this use the same store as whatever is the default
    or dominant store, but that's not a requirement. This store creates its own connection.
    '''

    # C0103: varnames and attrs must be >= 3 chars, but db defined by long time usage
    # pylint: disable = C0103
    def __init__(
        self, host, db, collection, port=27017, user=None, password=None,
        **kwargs
    ):
        '''
        Constructor
        '''
        self.db = pymongo.database.Database(
            pymongo.MongoClient(
                host=host,
                port=port,
                tz_aware=True,
                **kwargs
            ),
            db
        )
        if user is not None and password is not None:
            self.db.authenticate(user, password)

        self.location_map = self.db[collection + '.location_map']
        self.location_map.write_concern = {'w': 1}

    # location_map functions
    def create_map_entry(self, course_location, course_id=None, draft_branch='draft', prod_branch='published',
                         block_map=None):
        """
        Add a new entry to map this course_location to the new style CourseLocator.course_id. If course_id is not
        provided, it creates the default map of using org.course.name from the location (just like course_id) if
        the location.category = 'course'; otherwise, it uses org.course.

        You can create more than one mapping to the
        same course_id target. In that case, the reverse translate will be arbitrary (no guarantee of which wins).
        The use
        case for more than one mapping is to map both org/course/run and org/course to the same new course_id thus
        making a default for org/course. When querying for just org/course, the translator will prefer any entry
        which does not have a name in the _id; otherwise, it will return an arbitrary match.

        Note: the opposite is not true. That is, it never makes sense to use 2 different CourseLocator.course_id
        keys to index the same old Locator org/course/.. pattern. There's no checking to ensure you don't do this.

        NOTE: if there's already an entry w the given course_location, this may either overwrite that entry or
        throw an error depending on how mongo is configured.

        :param course_location: a Location preferably whose category is 'course'. Unlike the other
        map methods, this one doesn't take the old-style course_id.  It should be called with
        a course location not a block location; however, if called w/ a non-course Location, it creates
        a "default" map for the org/course pair to a new course_id.
        :param course_id: the CourseLocator style course_id
        :param draft_branch: the branch name to assign for drafts. This is hardcoded because old mongo had
        a fixed notion that there was 2 and only 2 versions for modules: draft and production. The old mongo
        did not, however, require that a draft version exist. The new one, however, does require a draft to
        exist.
        :param prod_branch: the branch name to assign for the production (live) copy. In old mongo, every course
        had to have a production version (whereas new split mongo does not require that until the author's ready
        to publish).
        :param block_map: an optional map to specify preferred names for blocks where the keys are the
        Location block names and the values are the BlockUsageLocator.block_id.
        """
        if course_id is None:
            if course_location.category == 'course':
                course_id = "{0.org}.{0.course}.{0.name}".format(course_location)
            else:
                course_id = "{0.org}.{0.course}".format(course_location)
        # very like _interpret_location_id but w/o the _id
        location_id = {'org': course_location.org, 'course': course_location.course}
        if course_location.category == 'course':
            location_id['name'] = course_location.name

        self.location_map.insert({
            '_id': location_id,
            'course_id': course_id,
            'draft_branch': draft_branch,
            'prod_branch': prod_branch,
            'block_map': block_map or {},
        })
        return course_id

    def translate_location(self, old_style_course_id, location, published=True, add_entry_if_missing=True):
        """
        Translate the given module location to a Locator. If the mapping has the run id in it, then you
        should provide old_style_course_id with that run id in it to disambiguate the mapping if there exists more
        than one entry in the mapping table for the org.course.

        The rationale for auto adding entries was that there should be a reasonable default translation
        if the code just trips into this w/o creating translations. The downfall is that ambiguous course
        locations may generate conflicting block_ids.

        Will raise ItemNotFoundError if there's no mapping and add_entry_if_missing is False.

        :param old_style_course_id: the course_id used in old mongo not the new one (optional, will use location)
        :param location:  a Location pointing to a module
        :param published: a boolean to indicate whether the caller wants the draft or published branch.
        :param add_entry_if_missing: a boolean as to whether to raise ItemNotFoundError or to create an entry if
        the course
        or block is not found in the map.

        NOTE: unlike old mongo, draft branches contain the whole course; so, it applies to all category
        of locations including course.
        """
        location_id = self._interpret_location_course_id(old_style_course_id, location)

        maps = self.location_map.find(location_id).sort('_id.name', pymongo.ASCENDING)
        if maps.count() == 0:
            if add_entry_if_missing:
                # create a new map
                course_location = location.replace(category='course', name=location_id['_id.name'])
                self.create_map_entry(course_location)
                entry = self.location_map.find_one(location_id)
            else:
                raise ItemNotFoundError()
        elif maps.count() > 1:
            # if more than one, prefer the one w/o a name if that exists. Otherwise, choose the first (alphabetically)
            entry = maps[0]
        else:
            entry = maps[0]

        if published:
            branch = entry['prod_branch']
        else:
            branch = entry['draft_branch']

        usage_id = entry['block_map'].get(self._encode_for_mongo(location.name))
        if usage_id is None:
            if add_entry_if_missing:
                usage_id = self._add_to_block_map(location, location_id, entry['block_map'])
            else:
                raise ItemNotFoundError(location)
        elif isinstance(usage_id, dict):
            # name is not unique, look through for the right category
            if location.category in usage_id:
                usage_id = usage_id[location.category]
            elif add_entry_if_missing:
                usage_id = self._add_to_block_map(location, location_id, entry['block_map'])
            else:
                raise ItemNotFoundError()
        else:
            raise InvalidLocationError()

        return BlockUsageLocator(course_id=entry['course_id'], branch=branch, usage_id=usage_id)

    def translate_locator_to_location(self, locator):
        """
        Returns an old style Location for the given Locator if there's an appropriate entry in the
        mapping collection. Note, it requires that the course was previously mapped (a side effect of
        translate_location or explicitly via create_map_entry) and
        the block's usage_id was previously stored in the
        map (a side effect of translate_location or via add|update_block_location).

        If there are no matches, it returns None.

        If there's more than one location to locator mapping to the same course_id, it looks for the first
        one with a mapping for the block usage_id and picks that arbitrary course location.

        :param locator: a BlockUsageLocator
        """
        # This does not require that the course exist in any modulestore
        # only that it has a mapping entry.
        maps = self.location_map.find({'course_id': locator.course_id})
        # look for one which maps to this block usage_id
        if maps.count() == 0:
            return None
        for candidate in maps:
            for old_name, cat_to_usage in candidate['block_map'].iteritems():
                for category, usage_id in cat_to_usage.iteritems():
                    if usage_id == locator.usage_id:
                        # figure out revision
                        # enforce the draft only if category in [..] logic
                        if category in draft.DIRECT_ONLY_CATEGORIES:
                            revision = None
                        elif locator.branch == candidate['draft_branch']:
                            revision = draft.DRAFT
                        else:
                            revision = None
                        return Location(
                            'i4x',
                            candidate['_id']['org'],
                            candidate['_id']['course'],
                            category,
                            self._decode_from_mongo(old_name),
                            revision)
        return None

    def add_block_location_translator(self, location, old_course_id=None, usage_id=None):
        """
        Similar to translate_location which adds an entry if none is found, but this cannot create a new
        course mapping entry, only a block within such a mapping entry. If it finds no existing
        course maps, it raises ItemNotFoundError.

        In the case that there are more than one mapping record for the course identified by location, this
        method adds the mapping to all matching records! (translate_location only adds to one)

        It allows the caller to specify
        the new-style usage_id for the target rather than having the translate concoct its own.
        If the provided usage_id already exists in one of the found maps for the org/course, this function
        raises DuplicateItemError unless the old item id == the new one.

        If the caller does not provide a usage_id and there exists an entry in one of the course variants,
        it will use that entry. If more than one variant uses conflicting entries, it will raise DuplicateItemError.

        Returns the usage_id used in the mapping

        :param location: a fully specified Location
        :param old_course_id: the old-style org/course or org/course/run string (optional)
        :param usage_id: the desired new block_id. If left as None, this will generate one as per translate_location
        """
        location_id = self._interpret_location_course_id(old_course_id, location)

        maps = self.location_map.find(location_id)
        if maps.count() == 0:
            raise ItemNotFoundError()

        # turn maps from cursor to list
        map_list = list(maps)
        encoded_location_name = self._encode_for_mongo(location.name)
        # check whether there's already a usage_id for this location (and it agrees w/ any passed in or found)
        for map_entry in map_list:
            if (encoded_location_name in map_entry['block_map'] and
                    location.category in map_entry['block_map'][encoded_location_name]):
                if usage_id is None:
                    usage_id = map_entry['block_map'][encoded_location_name][location.category]
                elif usage_id != map_entry['block_map'][encoded_location_name][location.category]:
                    raise DuplicateItemError(usage_id, self, 'location_map')

        computed_usage_id = usage_id

        # update the maps (and generate a usage_id if it's not been set yet)
        for map_entry in map_list:
            if computed_usage_id is None:
                computed_usage_id = self._add_to_block_map(location, location_id, map_entry['block_map'])
            elif (encoded_location_name not in map_entry['block_map'] or
                    location.category not in map_entry['block_map'][encoded_location_name]):
                alt_usage_id = self._verify_uniqueness(computed_usage_id, map_entry['block_map'])
                if alt_usage_id != computed_usage_id:
                    if usage_id is not None:
                        raise DuplicateItemError(usage_id, self, 'location_map')
                    else:
                        # revise already set ones and add to remaining ones
                        computed_usage_id = self.update_block_location_translator(
                            location,
                            alt_usage_id,
                            old_course_id,
                            True
                        )

                map_entry['block_map'].setdefault(encoded_location_name, {})[location.category] = computed_usage_id
                self.location_map.update({'_id': map_entry['_id']}, {'$set': {'block_map': map_entry['block_map']}})

        return computed_usage_id

    def update_block_location_translator(self, location, usage_id, old_course_id=None, autogenerated_usage_id=False):
        """
        Update all existing maps from location's block to the new usage_id. Used for changing the usage_id,
        thus the usage_id is required.

        Returns the usage_id. (which is primarily useful in the case of autogenerated_usage_id)

        :param location: a fully specified Location
        :param usage_id: the desired new block_id.
        :param old_course_id: the old-style org/course or org/course/run string (optional)
        :param autogenerated_usage_id: a flag used mostly for internal calls to indicate that this usage_id
        was autogenerated and thus can be overridden if it's not unique. If you set this flag, the stored
        usage_id may not be the one you submitted.
        """
        location_id = self._interpret_location_course_id(old_course_id, location)

        maps = self.location_map.find(location_id)
        encoded_location_name = self._encode_for_mongo(location.name)
        for map_entry in maps:
            # handle noop of renaming to same name
            if (encoded_location_name in map_entry['block_map'] and
                    map_entry['block_map'][encoded_location_name].get(location.category) == usage_id):
                continue
            alt_usage_id = self._verify_uniqueness(usage_id, map_entry['block_map'])
            if alt_usage_id != usage_id:
                if autogenerated_usage_id:
                    # revise already set ones and add to remaining ones
                    usage_id = self.update_block_location_translator(location, alt_usage_id, old_course_id, True)
                    return usage_id
                else:
                    raise DuplicateItemError(usage_id, self, 'location_map')

            if location.category in map_entry['block_map'].setdefault(encoded_location_name, {}):
                map_entry['block_map'][encoded_location_name][location.category] = usage_id
                self.location_map.update({'_id': map_entry['_id']}, {'$set': {'block_map': map_entry['block_map']}})

        return usage_id

    def delete_block_location_translator(self, location, old_course_id=None):
        """
        Remove all existing maps from location's block.

        :param location: a fully specified Location
        :param old_course_id: the old-style org/course or org/course/run string (optional)
        """
        location_id = self._interpret_location_course_id(old_course_id, location)

        maps = self.location_map.find(location_id)
        encoded_location_name = self._encode_for_mongo(location.name)
        for map_entry in maps:
            if location.category in map_entry['block_map'].setdefault(encoded_location_name, {}):
                if len(map_entry['block_map'][encoded_location_name]) == 1:
                    del map_entry['block_map'][encoded_location_name]
                else:
                    del map_entry['block_map'][encoded_location_name][location.category]
                self.location_map.update({'_id': map_entry['_id']}, {'$set': {'block_map': map_entry['block_map']}})

    def _add_to_block_map(self, location, location_id, block_map):
        '''add the given location to the block_map and persist it'''
        if self._block_id_is_guid(location.name):
            # This makes the ids more meaningful with a small probability of name collision.
            # The downside is that if there's more than one course mapped to from the same org/course root
            # the block ids will likely be out of sync and collide from an id perspective. HOWEVER,
            # if there are few == org/course roots or their content is unrelated, this will work well.
            usage_id = self._verify_uniqueness(location.category + location.name[:3], block_map)
        else:
            usage_id = location.name
        encoded_location_name = self._encode_for_mongo(location.name)
        block_map.setdefault(encoded_location_name, {})[location.category] = usage_id
        self.location_map.update(location_id, {'$set': {'block_map': block_map}})
        return usage_id

    def _interpret_location_course_id(self, course_id, location):
        """
        Take the old style course id (org/course/run) and return a dict for querying the mapping table.
        If the course_id is empty, it uses location, but this may result in an inadequate id.

        :param course_id: old style 'org/course/run' id from Location.course_id where Location.category = 'course'
        :param location: a Location object which may be to a module or a course. Provides partial info
        if course_id is omitted.
        """
        if course_id:
            # re doesn't allow ?P<_id.org> and ilk
            matched = re.match(r'([^/]+)/([^/]+)/([^/]+)', course_id)
            return dict(zip(['_id.org', '_id.course', '_id.name'], matched.groups()))

        location_id = {'_id.org': location.org, '_id.course': location.course}
        if location.category == 'course':
            location_id['_id.name'] = location.name
        return location_id

    def _block_id_is_guid(self, name):
        """
        Does the given name look like it's a guid?
        """
        return len(name) == 32 and re.search(r'[^0-9A-Fa-f]', name) is None

    def _verify_uniqueness(self, name, block_map):
        '''
        Verify that the name doesn't occur elsewhere in block_map. If it does, keep adding to it until
        it's unique.
        '''
        for targets in block_map.itervalues():
            if isinstance(targets, dict):
                for values in targets.itervalues():
                    if values == name:
                        name += str(randint(0, 9))
                        return self._verify_uniqueness(name, block_map)

            elif targets == name:
                name += str(randint(0, 9))
                return self._verify_uniqueness(name, block_map)
        return name

    def _encode_for_mongo(self, fieldname):
        """
        Fieldnames in mongo cannot have periods nor dollar signs. So encode them.
        :param fieldname: an atomic field name. Note, don't pass structured paths as it will flatten them
        """
        for char in [".", "$"]:
            fieldname = fieldname.replace(char, '%{:02x}'.format(ord(char)))
        return fieldname

    def _decode_from_mongo(self, fieldname):
        """
        The inverse of _encode_for_mongo
        :param fieldname: with period and dollar escaped
        """
        return urllib.unquote(fieldname)

