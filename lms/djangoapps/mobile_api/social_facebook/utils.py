"""
Common utility methods and decorators for Social Facebook APIs.
"""
import json
import urllib2
import facebook
from django.conf import settings
from social.apps.django_app.default.models import UserSocialAuth
from openedx.core.djangoapps.user_api.api.profile import preference_info
from rest_framework.response import Response
from rest_framework import status

_FACEBOOK_API_VERSION = settings.FACEBOOK_API_VERSION


def get_pagination(friends):
    '''
        Get paginated data from FaceBook response
    '''
    data = friends['data']
    while 'paging' in friends and 'next' in friends['paging']:
        response = urllib2.urlopen(friends['paging']['next'])
        friends = json.loads(response.read())
        data = data + friends['data']
    return data


def get_friends_from_facebook(serializer):
    '''
        Return the a list with the result of a facebook /me/friends call
        using the oauth_token contained within the serializer object.
        If facebook retruns an error return a response object containing
        the error message.
    '''
    try:
        graph = facebook.GraphAPI(serializer.object['oauth_token'])
        friends = graph.request(_FACEBOOK_API_VERSION + "/me/friends")
        return get_pagination(friends)
    except facebook.GraphAPIError, ex:
        return Response({'error': ex.result['error']['message']}, status=status.HTTP_400_BAD_REQUEST)


def get_linked_edx_accounts(data):
    '''
        Return a the list of friends from the input that are edx users with the
        additional attributes of edX_id and edX_username
    '''
    friends_that_are_edX_users = []
    for friend in data:
        query_set = UserSocialAuth.objects.filter(uid=unicode(friend['id']))
        if query_set.count() == 1:
            friend['edX_id'] = query_set[0].user_id
            friend['edX_username'] = query_set[0].user.username
            friends_that_are_edX_users.append(friend)
    return friends_that_are_edX_users


def share_with_facebook_friends(friend):
    '''
        Return true if the users sharing preferences are set to true
    '''
    share_fb_friends_settings = preference_info(friend['edX_username'])
    return ('share_with_facebook_friends' in share_fb_friends_settings) \
        and (share_fb_friends_settings['share_with_facebook_friends'] == 'True')
