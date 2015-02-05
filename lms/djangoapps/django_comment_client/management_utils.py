"""
This module provides utility functions for django_comment_client
"""
from pymongo.errors import PyMongoError
from pymongo import MongoClient

from django.contrib.auth.models import User


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
        client = MongoClient()
        db = client.forum
        db.users.update({'username': old_username}, {'$set': {'username': new_username}}, multi=False)
        db.contents.update({'author_username': old_username}, {'$set': {'author_username': new_username}}, multi=True)
    except PyMongoError:
        user.username = old_username
        user.save()
        raise
    return True
