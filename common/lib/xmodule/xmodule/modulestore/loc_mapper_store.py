'''
Method for converting among our differing Location/Locator whatever reprs
'''
from random import randint
import re
import pymongo
import bson.son

from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError
from xmodule.modulestore.locator import BlockUsageLocator
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

    def __init__(
        self, cache, host, db, collection, port=27017, user=None, password=None,
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
        self.cache = cache

    # location_map functions
    def create_map_entry(self, course_location, package_id=None, draft_branch='draft', prod_branch='published',
                         block_map=None):
        """
        Add a new entry to map this course_location to the new style CourseLocator.package_id. If package_id is not
        provided, it creates the default map of using org.course.name from the location if
        the location.category = 'course'; otherwise, it uses org.course.

        You can create more than one mapping to the
        same package_id target. In that case, the reverse translate will be arbitrary (no guarantee of which wins).
        The use
        case for more than one mapping is to map both org/course/run and org/course to the same new package_id thus
        making a default for org/course. When querying for just org/course, the translator will prefer any entry
        which does not have a name in the _id; otherwise, it will return an arbitrary match.

        Note: the opposite is not true. That is, it never makes sense to use 2 different CourseLocator.package_id
        keys to index the same old Locator org/course/.. pattern. There's no checking to ensure you don't do this.

        NOTE: if there's already an entry w the given course_location, this may either overwrite that entry or
        throw an error depending on how mongo is configured.

        :param course_location: a Location preferably whose category is 'course'. Unlike the other
        map methods, this one doesn't take the old-style course_id.  It should be called with
        a course location not a block location; however, if called w/ a non-course Location, it creates
        a "default" map for the org/course pair to a new package_id.
        :param package_id: the CourseLocator style package_id
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
        if package_id is None:
            if course_location.category == 'course':
                package_id = u"{0.org}.{0.course}.{0.name}".format(course_location)
            else:
                package_id = u"{0.org}.{0.course}".format(course_location)
        # very like _interpret_location_id but w/o the _id
        location_id = self._construct_location_son(
            course_location.org, course_location.course, 
            course_location.name if course_location.category == 'course' else None
        )

        self.location_map.insert({
            '_id': location_id,
            'course_id': package_id,
            'draft_branch': draft_branch,
            'prod_branch': prod_branch,
            'block_map': block_map or {},
        })
        return package_id

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
        if old_style_course_id is None:
            old_style_course_id = self._generate_location_course_id(location_id)

        cached_value = self._get_locator_from_cache(old_style_course_id, location, published)
        if cached_value:
            return cached_value

        maps = self.location_map.find(location_id)
        maps = list(maps)
        if len(maps) == 0:
            if add_entry_if_missing:
                # create a new map
                course_location = location.replace(category='course', name=location_id['_id']['name'])
                self.create_map_entry(course_location)
                entry = self.location_map.find_one(location_id)
            else:
                raise ItemNotFoundError()
        elif len(maps) == 1:
            entry = maps[0]
        else:
            # find entry w/o name, if any; otherwise, pick arbitrary
            entry = maps[0]
            for item in maps:
                if 'name' not in item['_id']:
                    entry = item
                    break

        block_id = entry['block_map'].get(self._encode_for_mongo(location.name))
        if block_id is None:
            if add_entry_if_missing:
                block_id = self._add_to_block_map(location, location_id, entry['block_map'])
            else:
                raise ItemNotFoundError(location)
        elif isinstance(block_id, dict):
            # name is not unique, look through for the right category
            if location.category in block_id:
                block_id = block_id[location.category]
            elif add_entry_if_missing:
                block_id = self._add_to_block_map(location, location_id, entry['block_map'])
            else:
                raise ItemNotFoundError()
        else:
            raise InvalidLocationError()

        published_usage = BlockUsageLocator(
            package_id=entry['course_id'], branch=entry['prod_branch'], block_id=block_id)
        draft_usage = BlockUsageLocator(
            package_id=entry['course_id'], branch=entry['draft_branch'], block_id=block_id)
        if published:
            result = published_usage
        else:
            result = draft_usage

        self._cache_location_map_entry(old_style_course_id, location, published_usage, draft_usage)
        return result


    def translate_locator_to_location(self, locator, get_course=False):
        """
        Returns an old style Location for the given Locator if there's an appropriate entry in the
        mapping collection. Note, it requires that the course was previously mapped (a side effect of
        translate_location or explicitly via create_map_entry) and
        the block's block_id was previously stored in the
        map (a side effect of translate_location or via add|update_block_location).

        If get_course, then rather than finding the map for this locator, it finds the 'course' root
        for the mapped course.

        If there are no matches, it returns None.

        If there's more than one location to locator mapping to the same package_id, it looks for the first
        one with a mapping for the block block_id and picks that arbitrary course location.

        :param locator: a BlockUsageLocator
        """
        if get_course:
            cached_value = self._get_course_location_from_cache(locator.package_id)
        else:
            cached_value = self._get_location_from_cache(locator)
        if cached_value:
            return cached_value

        # This does not require that the course exist in any modulestore
        # only that it has a mapping entry.
        maps = self.location_map.find({'course_id': locator.package_id})
        # look for one which maps to this block block_id
        if maps.count() == 0:
            return None
        result = None
        for candidate in maps:
            old_course_id = self._generate_location_course_id(candidate['_id'])
            for old_name, cat_to_usage in candidate['block_map'].iteritems():
                for category, block_id in cat_to_usage.iteritems():
                    # cache all entries and then figure out if we have the one we want
                    # Always return revision=None because the
                    # old draft module store wraps locations as draft before
                    # trying to access things.
                    location = Location(
                        'i4x',
                        candidate['_id']['org'],
                        candidate['_id']['course'],
                        category,
                        self._decode_from_mongo(old_name),
                        None)
                    published_locator = BlockUsageLocator(
                        candidate['course_id'], branch=candidate['prod_branch'], block_id=block_id
                    )
                    draft_locator = BlockUsageLocator(
                        candidate['course_id'], branch=candidate['draft_branch'], block_id=block_id
                    )
                    self._cache_location_map_entry(old_course_id, location, published_locator, draft_locator)
                    
                    if get_course and category == 'course':
                        result = location
                    elif not get_course and block_id == locator.block_id:
                        result = location
            if result is not None:
                return result
        return None

    def _add_to_block_map(self, location, location_id, block_map):
        '''add the given location to the block_map and persist it'''
        if self._block_id_is_guid(location.name):
            # This makes the ids more meaningful with a small probability of name collision.
            # The downside is that if there's more than one course mapped to from the same org/course root
            # the block ids will likely be out of sync and collide from an id perspective. HOWEVER,
            # if there are few == org/course roots or their content is unrelated, this will work well.
            block_id = self._verify_uniqueness(location.category + location.name[:3], block_map)
        else:
            # if 2 different category locations had same name, then they'll collide. Make the later
            # mapped ones unique
            block_id = self._verify_uniqueness(location.name, block_map)
        encoded_location_name = self._encode_for_mongo(location.name)
        block_map.setdefault(encoded_location_name, {})[location.category] = block_id
        self.location_map.update(location_id, {'$set': {'block_map': block_map}})
        return block_id

    def _interpret_location_course_id(self, course_id, location):
        """
        Take the old style course id (org/course/run) and return a dict w/ a SON for querying the mapping table.
        If the course_id is empty, it uses location, but this may result in an inadequate id.

        :param course_id: old style 'org/course/run' id from Location.course_id where Location.category = 'course'
        :param location: a Location object which may be to a module or a course. Provides partial info
        if course_id is omitted.
        """
        if course_id:
            # re doesn't allow ?P<_id.org> and ilk
            matched = re.match(r'([^/]+)/([^/]+)/([^/]+)', course_id)
            return {'_id': self._construct_location_son(*matched.groups())}

        if location.category == 'course':
            return {'_id': self._construct_location_son(location.org, location.course, location.name)}
        else:
            return bson.son.SON([('_id.org', location.org), ('_id.course', location.course)])
    
    def _generate_location_course_id(self, entry_id):
        """
        Generate a Location course_id for the given entry's id
        """
        # strip id envelope if any
        entry_id = entry_id.get('_id', entry_id)
        if entry_id.get('name', False):
            return u'{0[org]}/{0[course]}/{0[name]}'.format(entry_id)
        elif entry_id.get('_id.org', False):
            # the odd format one
            return u'{0[_id.org]}/{0[_id.course]}'.format(entry_id)
        else:
            return u'{0[org]}/{0[course]}'.format(entry_id)
    
    def _construct_location_son(self, org, course, name=None):
        """
        Construct the SON needed to repr the location for either a query or an insertion
        """
        if name:
            return bson.son.SON([('org', org), ('course', course), ('name', name)])
        else:
            return bson.son.SON([('org', org), ('course', course)])

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

    def _get_locator_from_cache(self, old_course_id, location, published):
        """
        See if the location x published pair is in the cache. If so, return the mapped locator.
        """
        entry = self.cache.get(u'{}+{}'.format(old_course_id, location.url()))
        if entry is not None:
            if published:
                return entry[0]
            else:
                return entry[1]
        return None

    def _get_location_from_cache(self, locator):
        """
        See if the locator is in the cache. If so, return the mapped location.
        """
        return self.cache.get(unicode(locator))

    def _get_course_location_from_cache(self, locator_package_id):
        """
        See if the package_id is in the cache. If so, return the mapped location to the
        course root.
        """
        return self.cache.get(u'courseId+{}'.format(locator_package_id))

    def _cache_location_map_entry(self, old_course_id, location, published_usage, draft_usage):
        """
        Cache the mapping from location to the draft and published Locators in entry.
        Also caches the inverse. If the location is category=='course', it caches it for
        the get_course query
        """
        setmany = {}
        if location.category == 'course':
            setmany[u'courseId+{}'.format(published_usage.package_id)] = location
        setmany[unicode(published_usage)] = location
        setmany[unicode(draft_usage)] = location
        setmany[u'{}+{}'.format(old_course_id, location.url())] = (published_usage, draft_usage)
        self.cache.set_many(setmany)
