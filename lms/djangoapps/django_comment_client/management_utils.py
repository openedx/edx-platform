"""
This module provides utility functions for django_comment_client
"""
from pymongo.errors import PyMongoError
from pymongo import MongoClient

from django.conf import settings
from django.contrib.auth.models import User

MONGO_PARAMS = settings.FORUM_MONGO_PARAMS


def get_mongo_connection_string():
    """
    Creates the a URI which contains the appropriate credentials needed to access MongoDB using MongoClient
    :return: a string representing the URI which can be used to create a MongoClient instance.
    """
    credentials = ''
    if MONGO_PARAMS['user'] != '':
        if MONGO_PARAMS['password'] == '':
            credentials = "{user}@".format(
                user=MONGO_PARAMS['user'],
            )
        else:
            credentials = "{user}:{password}@".format(
                user=MONGO_PARAMS['user'],
                password=MONGO_PARAMS['password'],
            )
    connection_string = "mongodb://" + credentials + "{host}:{port}/{database}".format(
        host=MONGO_PARAMS['host'],
        port=MONGO_PARAMS['port'],
        database=MONGO_PARAMS['database'],
    )
    return connection_string


def rename_user(old_username, new_username):
    """
    This function changes the username of a user
    :param old_username: old username of the user
    :param new_username: new username desired for this user
    :return: True if the command succeeds, otherwise an exception is bubbled up
    """
    user = User.objects.get(username=old_username)
    user.username = new_username
    user.save()
    try:
        client = MongoClient(get_mongo_connection_string())
        db = client[MONGO_PARAMS['database']]
        db.users.update({'username': old_username}, {'$set': {'username': new_username}}, multi=False)
        db.contents.update({'author_username': old_username}, {'$set': {'author_username': new_username}}, multi=True)
    except PyMongoError:
        user.username = old_username
        user.save()
        raise
    return True
