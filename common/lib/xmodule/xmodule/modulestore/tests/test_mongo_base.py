import unittest


class MongoBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.store = modulestore()
        self.store.create_course(org, course, run, user_id)

    def test_mongo_base_create_child_with_position(self):
        create_child(self, user_id, parent_usage_key, block_type, block_id=None, **kwargs):
