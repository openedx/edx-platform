'''
Test that computed fields (e.g., location) is not saved in the scope.content definition
'''
from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.mongo.base import location_to_query
from xblock.core import Scope


class TestFieldFilter(CourseTestCase):
    """
    Test that computed fields (e.g., location) is not saved in the scope.content definition
    """


    def testPreSplitMongo(self):
        """
        Test that the presplit mongo does the right thing
        """
        # course is persisted; so, check the db
        if isinstance(modulestore(), MongoModuleStore):
            item = modulestore('direct').collection.find_one(location_to_query(self.course.location))
            self.assertIsNotNone(item, "Can't get if it doesn't exist :-(")
            self.assertNotIn('location', item['definition']['data'])
            self.course.wiki_slug = 'a_different_slug'
            # change some content and ensure the filtered field didn't get saved
            modulestore('direct').update_item(
                self.course.location,
                self.course.get_explicitly_set_fields_by_scope(Scope.content)
            )
            item = modulestore('direct').collection.find_one(location_to_query(self.course.location))
            self.assertNotIn('location', item['definition']['data'])
