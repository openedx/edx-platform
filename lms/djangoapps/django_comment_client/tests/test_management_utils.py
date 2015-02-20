"""
Unit Tests for functions in the management_utils module
"""

import datetime
import unittest

from pymongo import MongoClient

from django.db import IntegrityError

from django.contrib.auth.models import User
from django.conf import settings

from student.tests.factories import UserFactory

from django_comment_client.management_utils import rename_user
from django_comment_client.management_utils import get_mongo_connection_string

MONGO_PARAMS = settings.FORUM_MONGO_PARAMS


class TestManagementUtils(unittest.TestCase):
    """
    These tests can be run from the terminal using the following command:
    python ./manage.py lms test --verbosity=1 lms/djangoapps/django_comment_client/tests/test_management_utils.py  --traceback --settings=test
    """
    NEW_USERNAME = 'targetName'

    def setUp(self):
        """
        loads 2 users and 2 comments (1 per user)
        """
        client = MongoClient(get_mongo_connection_string())
        self.db = client[MONGO_PARAMS['database']]
        # maintain arrays of mongo data so that we can delete them when the tests finish
        self.mongo_user_ids = []
        self.mongo_comment_ids = []
        self.sql_users = []
        self.seed_sql_users()
        self.seed_mongo_comments()
        self.seed_mongo_users()

    def seed_sql_users(self):
        """
        creates 2 users in the test sql database
        """
        self.sql_users.append(UserFactory.create())
        self.sql_users.append(UserFactory.create())

    def seed_mongo_comments(self):
        """
        creates 2 test comments (one for each user)
        """
        comment_1 = {
            "_type": "CommentThread",
            "abuse_flaggers": [],
            "anonymous": False,
            "anonymous_to_peers": False,
            "at_position_list": [],
            "author_id": "1",
            "author_username": self.sql_users[0].username,
            "body": "Architecto suscipit dolores. Velit enim quasi doloribus suscipit maxime laboriosam. Voluptatibus totam dolor dolorem dolorum placeat. Provident necessitatibus fugiat quia aut numquam repudiandae. Cum excepturi doloremque mollitia itaque eum praesentium.\n\nEx tempore maiores eum ea sed alias sint. Maiores veritatis commodi dolores aut et dolorem mollitia. Qui neque sed ea placeat.\n\nSit voluptas dicta et ut. Voluptas velit beatae veniam magni dolores. Est sed impedit numquam dolorum perspiciatis veniam. Temporibus inventore distinctio ratione labore nobis alias dolores. Est velit nihil dolorem qui nesciunt asperiores veritatis.",
            "closed": False,
            "comment_count": 9,
            "commentable_id": "video_1",
            "course_id": "MITx/6.002x/2012_Fall",
            "created_at": datetime.datetime.strptime('22092013', "%d%m%Y"),
            "historical_abuse_flaggers": [],
            "last_activity_at": datetime.datetime.strptime('22092013', "%d%m%Y"),
            "tags_array": [
                "c#",
                "2012",
                "java-sucks",
            ],
            "thread_type": "discussion",
            "title": "Dolore et molestias quia maxime eaque quos voluptatem et.",
            "updated_at": datetime.datetime.strptime('22092013', "%d%m%Y"),
            "visible": True,
            "votes": {
                "count": 7,
                "down": [
                    "1",
                    "3",
                    "4",
                    "5",
                    "7",
                ],
                "down_count": 5,
                "point": -3,
                "up": [
                    "2",
                    "6",
                ],
                "up_count": 2,
            }
        }

        comment_2 = {
            "_type": "Comment",
            "abuse_flaggers": [],
            "anonymous": False,
            "anonymous_to_peers": False,
            "at_position_list": [],
            "author_id": "2",
            "author_username": self.sql_users[1].username,
            "body": "Tempora quis molestias unde. Dolore facilis tenetur repellendus quia labore doloribus molestiae.",
            "comment_thread_id": "523e7ed87b36b70200000001",
            "course_id": "MITx/6.002x/2012_Fall",
            "created_at": datetime.datetime.strptime('22092013', "%d%m%Y"),
            "endorsed": False,
            "historical_abuse_flaggers": [],
            "parent_ids": [],
            "sk": "523e7ed87b36b70200000005",
            "updated_at": datetime.datetime.strptime('22092013', "%d%m%Y"),
            "visible": True,
            "votes": {
                "count": 7,
                "down": [
                    "3",
                    "5",
                    "6",
                    "7",
                ],
                "down_count": 4,
                "point": -1,
                "up": [
                    "1",
                    "2",
                    "4",
                ],
                "up_count": 3,
            }
        }
        self.mongo_comment_ids.append(self.db.contents.insert(comment_1))
        self.mongo_comment_ids.append(self.db.contents.insert(comment_2))

    def seed_mongo_users(self):
        """
        create 2 test users
        """
        user_1 = {
            "default_sort_key": "date",
            "notification_ids": [],
            "external_id": self.sql_users[0].username,
            "username": self.sql_users[0].username,
        }
        user_2 = {
            "default_sort_key": "date",
            "email": "robot2@robots.com",
            "external_id": self.sql_users[1].username,
            "notification_ids": [],
            "read_states": [
                {
                    "_id": "5410bb0d9fbe726175000002",
                    "course_id": "Carnegie/Training/CLASlite",
                    "last_read_times": {
                        "5410bb0a9fbe727505000001": datetime.datetime.strptime('10092014', "%d%m%Y"),
                        "541b0ef870da966ba5000001": datetime.datetime.strptime('10092014', "%d%m%Y"),
                    },
                },
            ],
            "username": self.sql_users[1].username,
        }
        self.mongo_user_ids.append(self.db.users.insert(user_1))
        self.mongo_user_ids.append(self.db.users.insert(user_2))

    def test_user_not_found(self):
        """
        ensures that the rename_user tool throws an exception when the user for a given username does not exist
        """
        self.assertEqual(0, len(User.objects.filter(username='---@---.com')))
        self.assertRaises(User.DoesNotExist, rename_user, '---@---.com', '---2@---2.com')

    def test_integrity_error(self):
        """
        ensures that an error is thrown when two users have the same username
        """
        self.assertRaises(IntegrityError, rename_user, self.sql_users[0].username, self.sql_users[1].username)

    def test_rename_user(self):
        """
        ensures that the rename_user utility successfully renames a user
        """
        # ensure that the starting sql username is different from the target username
        self.assertNotEqual(self.sql_users[0].username, TestManagementUtils.NEW_USERNAME)

        # ensure that the starting mongo username matches the starting sql username
        mongo_user = self.db.users.find_one({'username': self.sql_users[0].username})
        self.assertEqual(mongo_user['username'], self.sql_users[0].username)
        mongo_comment = self.db.contents.find_one({'author_username': self.sql_users[0].username})
        self.assertEqual(mongo_comment['author_username'], self.sql_users[0].username)

        # perform the rename
        result = rename_user(self.sql_users[0].username, TestManagementUtils.NEW_USERNAME)

        self.assertTrue(result)
        # check that the sql username now matches the target username
        self.sql_users[0] = User.objects.get(id=self.sql_users[0].id)
        self.assertEqual(self.sql_users[0].username, TestManagementUtils.NEW_USERNAME)

        # check that the mongo username now matches the target username
        mongo_user = self.db.users.find_one({'_id': mongo_user['_id']})
        self.assertEqual(mongo_user['username'], TestManagementUtils.NEW_USERNAME)

        mongo_comment = self.db.contents.find_one({'_id': mongo_comment['_id']})
        self.assertEqual(mongo_comment['author_username'], TestManagementUtils.NEW_USERNAME)

    def test_rename_not_matching(self):
        """
        ensure that the username for the second user does not change when renaming the first user
        """
        # check that the username for user2 is initially different from the new username
        self.assertNotEqual(self.sql_users[1].username, TestManagementUtils.NEW_USERNAME)
        mongo_user2 = self.db.users.find_one({'username': self.sql_users[1].username})
        mongo_comment2 = self.db.contents.find_one({'author_username': self.sql_users[1].username})
        self.assertEqual(mongo_user2['username'], self.sql_users[1].username)
        self.assertEqual(mongo_comment2['author_username'], self.sql_users[1].username)

        # perform the rename only for the first user
        result = rename_user(self.sql_users[0].username, TestManagementUtils.NEW_USERNAME)
        # ensure that another user was successfully changed
        self.assertTrue(result)

        # re-query the second user
        self.sql_users[1] = User.objects.get(id=self.sql_users[1].id)
        mongo_user2 = self.db.users.find_one({'_id': mongo_user2['_id']})
        mongo_comment2 = self.db.contents.find_one({'_id': mongo_comment2['_id']})

        # check that the rename operation did not change the username for user2 to the new username
        self.assertNotEqual(self.sql_users[1].username, TestManagementUtils.NEW_USERNAME)
        self.assertNotEqual(mongo_user2['username'], TestManagementUtils.NEW_USERNAME)
        self.assertNotEqual(mongo_comment2['author_username'], TestManagementUtils.NEW_USERNAME)

    def tearDown(self):
        """
        removes all test data
        """
        for user_id in self.mongo_user_ids:
            self.db.users.remove({"_id": user_id})
        for comment_id in self.mongo_comment_ids:
            self.db.contents.remove({"_id": comment_id})
        User.objects.all().delete()
