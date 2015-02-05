"""
Unit Tests for the manage.py command rename_user
"""

import unittest
import datetime

from pymongo import MongoClient

from django.core.management.base import CommandError

from django.contrib.auth.models import User

from student.tests.factories import UserFactory

from django_comment_client.management.commands import rename_user


class TestManagementCommandsRenameUser(unittest.TestCase):
    """
    Verify functionality of `rename_user` management command
    These tests can be run from the terminal using the following command:
    python ./manage.py lms test --verbosity=1 lms/djangoapps/django_comment_client/tests/test_management_commands_rename_user.py  --traceback --settings=test

    """
    def setUp(self):
        """
        load a user and comment into the db for testing purposes
        """
        client = MongoClient()
        self.db = client.forum
        self.mongo_user_id = None
        self.mongo_comment_id = None
        self.sql_user = UserFactory.create()
        self.rename_cmd = rename_user.Command()
        self.seed_mongo_comment()
        self.seed_mongo_user()

    def seed_mongo_comment(self):
        """
        Seeds a test comment object that belongs to a test user
        """
        comment = {
            "_type": "CommentThread",
            "abuse_flaggers": [],
            "anonymous": False,
            "anonymous_to_peers": False,
            "at_position_list": [],
            "author_id": "1",
            "author_username": self.sql_user.username,
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
        self.mongo_comment_id = self.db.contents.insert(comment)

    def seed_mongo_user(self):
        """
        Seeds a test  user
        """
        user = {
            "default_sort_key": "date",
            "notification_ids": [],
            "external_id": self.sql_user.username,
            "username": self.sql_user.username,
        }
        self.mongo_user_id = self.db.users.insert(user)

    def test_incorrect_num_args(self):
        """
        ensures that the command line tools does not work with an incorrect number of arguments
        """
        for i in [0, 1, 3]:
            args = ['arg'] * i
            self.assertRaises(CommandError, self.rename_cmd.handle, *args)

    def test_successful_change(self):
        """
        runs the command line tools and ensures successful rename
        """
        username_old = self.sql_user.username
        username_new = username_old + '2'
        self.assertEqual(0, len(User.objects.filter(
            username=username_new
        )))
        self.rename_cmd.handle(username_old, username_new)

    def tearDown(self):
        """
        removes all test data
        """
        self.db.users.remove({"_id": self.mongo_user_id})
        self.db.contents.remove({"_id": self.mongo_comment_id})
        User.objects.all().delete()
