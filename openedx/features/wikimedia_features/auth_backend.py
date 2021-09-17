import logging
from django.utils.functional import cached_property
from social_core.exceptions import AuthException
from common.djangoapps.third_party_auth.identityserver3 import IdentityServer3

log = logging.getLogger(__name__)


class WikimediaIdentityServer(IdentityServer3):
    """
    An extension of the IdentityServer3 for use with Wikimedia's IdP service.
    """
    name = "wikimediaIdentityServer"
    DEFAULT_SCOPE = ["mwoauth-authonlyprivate"]
    ID_KEY = "sub"

    def _parse_name(self, name):
        fullname = name
        if ' ' in fullname:
            firstname, lastname = fullname.split(' ', 1)
        else:
            firstname = name
            lastname = ""
        return fullname, firstname, lastname

    def get_user_details(self, response):
        """
        Returns detail about the user account from the service
        """

        try:
            name = response.get("realname", "") or response["username"]
            fullname, firstname, lastname = self._parse_name(name)

            details = {
                "fullname": fullname,
                "email": response["email"],
                "first_name": firstname,
                "last_name": lastname,
                "username": response["username"]
            }
            return details
        except KeyError:
            log.exception("User profile data is unappropriate or not given")
            raise AuthException("Wikimedia", "User profile data is unappropriate or not given")

    @cached_property
    def _id3_config(self):
        from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
        return OAuth2ProviderConfig.current(self.name)
