"""
Common utility methods and decorators for Social Facebook APIs.
"""
import json
import urllib2
import facebook
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
from social.apps.django_app.default.models import UserSocialAuth
from openedx.core.djangoapps.user_api.models import UserPreference
from student.models import User


# TODO
# The pagination strategy needs to be further flushed out.
# What is the default page size for the facebook Graph API? 25? Is the page size a parameter that can be tweaked?
# If a user has a large number of friends, we would be calling the FB API num_friends/page_size times.
#
# However, on the app, we don't plan to display all those friends anyway.
# If we do, for scalability, the endpoints themselves would need to be paginated.
def get_pagination(friends):
    """
    Get paginated data from FaceBook response
    """
    data = friends['data']
    while 'paging' in friends and 'next' in friends['paging']:
        response = urllib2.urlopen(friends['paging']['next'])
        friends = json.loads(response.read())
        data = data + friends['data']
    return data


def get_friends_from_facebook(serializer):
    """
    Return a list with the result of a facebook /me/friends call
    using the oauth_token contained within the serializer object.
    If facebook returns an error, return a response object containing
    the error message.
    """
    try:
        graph = facebook.GraphAPI(serializer.data['oauth_token'])
        friends = graph.request(settings.FACEBOOK_API_VERSION + "/me/friends")
        return get_pagination(friends)
    except facebook.GraphAPIError, ex:
        return Response({'error': ex.result['error']['message']}, status=status.HTTP_400_BAD_REQUEST)


def get_linked_edx_accounts(data):
    """
    Return a list of friends from the input that are edx users with the
    additional attributes of edX_id and edX_username
    """
    friends_that_are_edx_users = []
    for friend in data:
        query_set = UserSocialAuth.objects.filter(uid=unicode(friend['id']))
        if query_set.count() == 1:
            friend['edX_id'] = query_set[0].user_id
            friend['edX_username'] = query_set[0].user.username
            friends_that_are_edx_users.append(friend)
    return friends_that_are_edx_users


def share_with_facebook_friends(friend):
    """
    Return true if the user's share_with_facebook_friends preference is set to true.
    """

    # Calling UserPreference directly because the requesting user may be different (and not is_staff).
    try:
        existing_user = User.objects.get(username=friend['edX_username'])
    except ObjectDoesNotExist:
        return False

    return UserPreference.get_value(existing_user, 'share_with_facebook_friends') == 'True'
