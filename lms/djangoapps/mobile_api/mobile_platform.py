"""
Platform related Operations for Mobile APP
"""


import abc
import re

import six


class MobilePlatform(six.with_metaclass(abc.ABCMeta)):
    """
    MobilePlatform class creates an instance of platform based on user agent and supports platform
    related operations.
    """
    version = None

    def __init__(self, version):
        self.version = version

    @classmethod
    def get_user_app_platform(cls, user_agent, user_agent_regex):
        """
        Returns platform instance if user_agent matches with USER_AGENT_REGEX

        Arguments:
            user_agent (str): user-agent for mobile app making the request.
            user_agent_regex (regex str): Regex for user-agent valid for any type pf mobile platform.

        Returns:
           An instance of class passed (which would be one of the supported mobile platform
           classes i.e. PLATFORM_CLASSES) if user_agent matches regex of that class else returns None
        """
        match = re.search(user_agent_regex, user_agent)
        if match:
            return cls(match.group('version'))

    @classmethod
    def get_instance(cls, user_agent):
        """
        It creates an instance of one of the supported mobile platforms (i.e. iOS, Android) by regex comparison
        of user-agent.

        Parameters:
            user_agent: user_agent of mobile app

        Returns:
            instance of one of the supported mobile platforms (i.e. iOS, Android)
        """
        for subclass in PLATFORM_CLASSES.values():
            instance = subclass.get_user_app_platform(user_agent, subclass.USER_AGENT_REGEX)
            if instance:
                return instance


class IOS(MobilePlatform):
    """ iOS platform """
    USER_AGENT_REGEX = (r'\((?P<version>[0-9]+.[0-9]+.[0-9]+(\.[0-9a-zA-Z]*)?); OS Version [0-9.]+ '
                        r'\(Build [0-9a-zA-Z]*\)\)')
    NAME = u"iOS"


class Android(MobilePlatform):
    """ Android platform """
    USER_AGENT_REGEX = (r'Dalvik/[.0-9]+ \(Linux; U; Android [.0-9]+; (.*) (Build|MIUI)/[0-9a-zA-Z-.]*\) '
                        r'(.*)/(?P<version>[0-9]+.[0-9]+.[0-9]+(\.[0-9a-zA-Z]*)?)')
    NAME = u"Android"


# a list of all supported mobile platforms
PLATFORM_CLASSES = {IOS.NAME: IOS, Android.NAME: Android}
