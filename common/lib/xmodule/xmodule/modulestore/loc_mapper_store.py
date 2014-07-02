'''
Method for converting among our differing Location/Locator whatever reprs
'''
from random import randint
import re
import pymongo
import bson.son
import urllib

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.keys import CourseKey


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

    SCHEMA_VERSION = 1
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
                document_class=bson.son.SON,
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
    def create_map_entry(self, course_key, org=None, course=None, run=None,
                         draft_branch=ModuleStoreEnum.BranchName.draft,
                         prod_branch=ModuleStoreEnum.BranchName.published,
                         block_map=None):
        """
        Add a new entry to map this SlashSeparatedCourseKey to the new style CourseLocator.org & course & run. If
        org and course and run are not provided, it defaults them based on course_key.

        WARNING: Exactly 1 CourseLocator key should index a given SlashSeparatedCourseKey.
        We provide no mechanism to enforce this assertion.

        NOTE: if there's already an entry w the given course_key, this may either overwrite that entry or
        throw an error depending on how mongo is configured.

        :param course_key (SlashSeparatedCourseKey): a SlashSeparatedCourseKey
        :param org (string): the CourseLocator style org
        :param course (string): the CourseLocator course number
        :param run (string): the CourseLocator run of this course
        :param draft_branch: the branch name to assign for drafts. This is hardcoded because old mongo had
        a fixed notion that there was 2 and only 2 versions for modules: draft and production. The old mongo
        did not, however, require that a draft version exist. The new one, however, does require a draft to
        exist.
        :param prod_branch: the branch name to assign for the production (live) copy. In old mongo, every course
        had to have a production version (whereas new split mongo does not require that until the author's ready
        to publish).
        :param block_map: an optional map to specify preferred names for blocks where the keys are the
        Location block names and the values are the BlockUsageLocator.block_id.

        Returns:
            :class:`CourseLocator` representing the new id for the course

        Raises:
            ValueError if one and only one of org and course and run is provided. Provide all of them or none of them.
        """
        if org is None and course is None and run is None:
            assert(isinstance(course_key, CourseKey))
            org = course_key.org
            course = course_key.course
            run = course_key.run
        elif org is None or course is None or run is None:
            raise ValueError(
                u"Either supply org, course and run or none of them. Not just some of them: {}, {}, {}".format(org, course, run)
            )

        # very like _interpret_location_id but using mongo subdoc lookup (more performant)
        course_son = self._construct_course_son(course_key)

        self.location_map.insert({
            '_id': course_son,
            'org': org,
            'course': course,
            'run': run,
            'draft_branch': draft_branch,
            'prod_branch': prod_branch,
            'block_map': block_map or {},
            'schema': self.SCHEMA_VERSION,
        })

        return CourseLocator(org, course, run)

    def translate_location(self, location, published=True,
                           add_entry_if_missing=True, passed_block_id=None):
        """
        Translate the given module location to a Locator.

        The rationale for auto adding entries was that there should be a reasonable default translation
        if the code just trips into this w/o creating translations.

        Will raise ItemNotFoundError if there's no mapping and add_entry_if_missing is False.

        :param location:  a Location pointing to a module
        :param published: a boolean to indicate whether the caller wants the draft or published branch.
        :param add_entry_if_missing: a boolean as to whether to raise ItemNotFoundError or to create an entry if
        the course
        or block is not found in the map.
        :param passed_block_id: what block_id to assign and save if none is found
        (only if add_entry_if_missing)

        NOTE: unlike old mongo, draft branches contain the whole course; so, it applies to all category
        of locations including course.
        """
        course_son = self._interpret_location_course_id(location.course_key)

        cached_value = self._get_locator_from_cache(location, published)
        if cached_value:
            return cached_value

        entry = self.location_map.find_one(course_son)
        if entry is None:
            if add_entry_if_missing:
                # create a new map
                self.create_map_entry(location.course_key)
                entry = self.location_map.find_one(course_son)
            else:
                raise ItemNotFoundError(location)
        else:
            entry = self._migrate_if_necessary([entry])[0]

        block_id = entry['block_map'].get(self.encode_key_for_mongo(location.name))
        category = location.category
        if block_id is None:
            if add_entry_if_missing:
                block_id = self._add_to_block_map(
                    location, course_son, entry['block_map'], passed_block_id
                )
            else:
                raise ItemNotFoundError(location)
        else:
            # jump_to_id uses a None category.
            if category is None:
                if len(block_id) == 1:
                    # unique match (most common case)
                    category = block_id.keys()[0]
                    block_id = block_id.values()[0]
                else:
                    raise InvalidLocationError()
            elif category in block_id:
                block_id = block_id[category]
            elif add_entry_if_missing:
                block_id = self._add_to_block_map(location, course_son, entry['block_map'])
            else:
                raise ItemNotFoundError(location)

        prod_course_locator = CourseLocator(
            org=entry['org'],
            course=entry['course'],
            run=entry['run'],
            branch=entry['prod_branch']
        )
        published_usage = BlockUsageLocator(
            prod_course_locator,
            block_type=category,
            block_id=block_id
        )
        draft_usage = BlockUsageLocator(
            prod_course_locator.for_branch(entry['draft_branch']),
            block_type=category,
            block_id=block_id
        )
        if published:
            result = published_usage
        else:
            result = draft_usage

        self._cache_location_map_entry(location, published_usage, draft_usage)
        return result

    def translate_locator_to_location(self, locator, get_course=False):
        """
        Returns an old style Location for the given Locator if there's an appropriate entry in the
        mapping collection. Note, it requires that the course was previously mapped (a side effect of
        translate_location or explicitly via create_map_entry) and
        the block's block_id was previously stored in the
        map (a side effect of translate_location or via add|update_block_location).

        If there are no matches, it returns None.

        Args:
            locator: a BlockUsageLocator to translate
            get_course: rather than finding the map for this locator, returns the CourseKey
                for the mapped course.
        """
        if get_course:
            cached_value = self._get_course_location_from_cache(
                # if locator is already a course_key it won't have course_key attr
                getattr(locator, 'course_key', locator)
            )
        else:
            cached_value = self._get_location_from_cache(locator)
        if cached_value:
            return cached_value

        # migrate any records which don't have the org and course and run fields as
        # this won't be able to find what it wants. (only needs to be run once ever per db,
        # I'm not sure how to control that, but I'm putting some check here for once per launch)
        if not getattr(self, 'offering_migrated', False):
            obsolete = self.location_map.find(
                {'org': {"$exists": False}, "offering": {"$exists": False}, }
            )
            self._migrate_if_necessary(obsolete)
            setattr(self, 'offering_migrated', True)

        entry = self.location_map.find_one(bson.son.SON([
            ('org', locator.org),
            ('course', locator.course),
            ('run', locator.run),
        ]))

        # look for one which maps to this block block_id
        if entry is None:
            return None
        old_course_id = self._generate_location_course_id(entry['_id'])
        if get_course:
            return old_course_id

        for old_name, cat_to_usage in entry['block_map'].iteritems():
            for category, block_id in cat_to_usage.iteritems():
                # cache all entries and then figure out if we have the one we want
                # Always return revision=MongoRevisionKey.published because the
                # old draft module store wraps locations as draft before
                # trying to access things.
                location = old_course_id.make_usage_key(
                    category,
                    self.decode_key_from_mongo(old_name)
                )

                entry_org = "org"
                entry_course = "course"
                entry_run = "run"

                published_locator = BlockUsageLocator(
                    CourseLocator(
                        org=entry[entry_org],
                        course=entry[entry_course],
                        run=entry[entry_run],
                        branch=entry['prod_branch']
                    ),
                    block_type=category,
                    block_id=block_id
                )
                draft_locator = BlockUsageLocator(
                    CourseLocator(
                        org=entry[entry_org], course=entry[entry_course], run=entry[entry_run],
                        branch=entry['draft_branch']
                    ),
                    block_type=category,
                    block_id=block_id
                )
                self._cache_location_map_entry(location, published_locator, draft_locator)

                if block_id == locator.block_id:
                    return location

        return None

    def translate_location_to_course_locator(self, course_key, published=True):
        """
        Used when you only need the CourseLocator and not a full BlockUsageLocator. Probably only
        useful for get_items which wildcards name or category.

        :param course_key: a CourseKey
        :param published: a boolean representing whether or not we should return the published or draft version

        Returns a Courselocator
        """
        cached = self._get_course_locator_from_cache(course_key, published)
        if cached:
            return cached

        course_son = self._interpret_location_course_id(course_key)

        entry = self.location_map.find_one(course_son)
        if entry is None:
            raise ItemNotFoundError(course_key)

        published_course_locator = CourseLocator(
            org=entry['org'], course=entry['course'], run=entry['run'], branch=entry['prod_branch']
        )
        draft_course_locator = CourseLocator(
            org=entry['org'], course=entry['course'], run=entry['run'], branch=entry['draft_branch']
        )
        self._cache_course_locator(course_key, published_course_locator, draft_course_locator)
        if published:
            return published_course_locator
        else:
            return draft_course_locator

    def _add_to_block_map(self, location, course_son, block_map, block_id=None):
        '''add the given location to the block_map and persist it'''
        if block_id is None:
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
        encoded_location_name = self.encode_key_for_mongo(location.name)
        block_map.setdefault(encoded_location_name, {})[location.category] = block_id
        self.location_map.update(course_son, {'$set': {'block_map': block_map}})
        return block_id

    def _interpret_location_course_id(self, course_key):
        """
        Take a CourseKey and return a SON for querying the mapping table.

        :param course_key: a CourseKey object for a course.
        """
        return {'_id': self._construct_course_son(course_key)}

    def _generate_location_course_id(self, entry_id):
        """
        Generate a CourseKey for the given entry's id.
        """
        return SlashSeparatedCourseKey(entry_id['org'], entry_id['course'], entry_id['name'])

    def _construct_course_son(self, course_key):
        """
        Construct the SON needed to repr the course_key for either a query or an insertion
        """
        assert(isinstance(course_key, CourseKey))
        return bson.son.SON([
            ('org', course_key.org),
            ('course', course_key.course),
            ('name', course_key.run)
        ])

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

    @staticmethod
    def encode_key_for_mongo(fieldname):
        """
        Fieldnames in mongo cannot have periods nor dollar signs. So encode them.
        :param fieldname: an atomic field name. Note, don't pass structured paths as it will flatten them
        """
        for char in [".", "$"]:
            fieldname = fieldname.replace(char, '%{:02x}'.format(ord(char)))
        return fieldname

    @staticmethod
    def decode_key_from_mongo(fieldname):
        """
        The inverse of encode_key_for_mongo
        :param fieldname: with period and dollar escaped
        """
        return urllib.unquote(fieldname)

    def _get_locator_from_cache(self, location, published):
        """
        See if the location x published pair is in the cache. If so, return the mapped locator.
        """
        entry = self.cache.get(u'{}+{}'.format(location.course_key, location))
        if entry is not None:
            if published:
                return entry[0]
            else:
                return entry[1]
        return None

    def _get_course_locator_from_cache(self, old_course_id, published):
        """
        Get the course Locator for this old course id
        """
        if not old_course_id:
            return None
        entry = self.cache.get(unicode(old_course_id))
        if entry is not None:
            if published:
                return entry[0].course_key
            else:
                return entry[1].course_key

    def _get_location_from_cache(self, locator):
        """
        See if the locator is in the cache. If so, return the mapped location.
        """
        return self.cache.get(unicode(locator))

    def _get_course_location_from_cache(self, course_key):
        """
        See if the course_key is in the cache. If so, return the mapped location to the
        course root.
        """
        cache_key = self._course_key_cache_string(course_key)
        return self.cache.get(cache_key)

    def _course_key_cache_string(self, course_key):
        """
        Return the string used to cache the course key
        """
        return u'{0.org}+{0.course}+{0.run}'.format(course_key)

    def _cache_course_locator(self, old_course_id, published_course_locator, draft_course_locator):
        """
        For quick lookup of courses
        """
        if not old_course_id:
            return
        self.cache.set(unicode(old_course_id), (published_course_locator, draft_course_locator))

    def _cache_location_map_entry(self, location, published_usage, draft_usage):
        """
        Cache the mapping from location to the draft and published Locators in entry.
        Also caches the inverse. If the location is category=='course', it caches it for
        the get_course query
        """
        setmany = {}
        if location.category == 'course':
            setmany[self._course_key_cache_string(published_usage)] = location.course_key
        setmany[unicode(published_usage)] = location
        setmany[unicode(draft_usage)] = location
        setmany[unicode(location)] = (published_usage, draft_usage)
        setmany[unicode(location.course_key)] = (published_usage, draft_usage)
        self.cache.set_many(setmany)

    def delete_course_mapping(self, course_key):
        """
        Remove provided course location from loc_mapper and cache.

        :param course_key: a CourseKey for the course we wish to delete
        """
        self.location_map.remove(self._interpret_location_course_id(course_key))

        # Remove the location of course (draft and published) from cache
        cached_key = self.cache.get(unicode(course_key))
        if cached_key:
            delete_keys = []
            published_locator = unicode(cached_key[0].course_key)
            course_location = self._course_location_from_cache(published_locator)
            delete_keys.append(self._course_key_cache_string(course_key))
            delete_keys.append(published_locator)
            delete_keys.append(unicode(cached_key[1].course_key))
            delete_keys.append(unicode(course_location))
            delete_keys.append(unicode(course_key))
            self.cache.delete_many(delete_keys)

    def _migrate_if_necessary(self, entries):
        """
        Run the entries through any applicable schema updates and return the updated entries
        """
        entries = [
            self._migrate[entry.get('schema', 0)](self, entry)
            for entry in entries
        ]
        return entries

    def _entry_id_to_son(self, entry_id):
        return bson.son.SON([
            ('org', entry_id['org']),
            ('course', entry_id['course']),
            ('name', entry_id['name'])
        ])

    def _delete_cache_location_map_entry(self, old_course_id, location, published_usage, draft_usage):
        """
        Remove the location of course (draft and published) from cache
        """
        delete_keys = []
        if location.category == 'course':
            delete_keys.append(self._course_key_cache_string(published_usage.course_key))

        delete_keys.append(unicode(published_usage))
        delete_keys.append(unicode(draft_usage))
        delete_keys.append(u'{}+{}'.format(old_course_id, location.to_deprecated_string()))
        delete_keys.append(old_course_id)
        self.cache.delete_many(delete_keys)

    def _migrate_top(self, entry, updated=False):
        """
        Current version, so a no data change until next update. But since it's the top
        it's responsible for persisting the record if it changed.
        """
        if updated:
            entry['schema'] = self.SCHEMA_VERSION
            entry_id = self._entry_id_to_son(entry['_id'])
            self.location_map.update({'_id': entry_id}, entry)

        return entry

    def _migrate_0(self, entry):
        """
        If entry had an '_id' without a run, remove the whole record.

        Add fields: schema, org, course, run
        Remove: course_id, lower_course_id
        :param entry:
        """
        if 'name' not in entry['_id']:
            entry_id = entry['_id']
            entry_id = bson.son.SON([
                ('org', entry_id['org']),
                ('course', entry_id['course']),
            ])
            self.location_map.remove({'_id': entry_id})
            return None

        # add schema, org, course, run, etc, remove old fields
        entry['schema'] = 0
        entry.pop('course_id', None)
        entry.pop('lower_course_id', None)
        old_course_id = SlashSeparatedCourseKey(entry['_id']['org'], entry['_id']['course'], entry['_id']['name'])
        entry['org'] = old_course_id.org
        entry['course'] = old_course_id.course
        entry['run'] = old_course_id.run
        return self._migrate_1(entry, True)

    # insert new migrations just before _migrate_top. _migrate_top sets the schema version and
    # saves the record
    _migrate = [_migrate_0, _migrate_top]
