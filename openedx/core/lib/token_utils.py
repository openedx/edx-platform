"""
Deprecated JwtBuilder class for backward compatibility until edx-enterprise is updated.
"""
from openedx.core.djangoapps.oauth_dispatch.jwt import create_api_client_jwt


class JwtBuilder(object):
    """
    Deprecated. Use openedx.core.djangoapps.oauth_dispatch.jwt.JwtBuilder directly.
    """
    def __init__(self, user, secret=None):
        self.user = user
        self.secret = secret

    def build_token(
        self,
        scopes=None,  # pylint: disable=unused-argument
        expires_in=None,  # pylint: disable=unused-argument
        aud=None,
        additional_claims=None,
    ):
        """
        Deprecated. Use openedx.core.djangoapps.oauth_dispatch.jwt.JwtBuilder directly.
        For backward compatibility reasons only.
        """
        return create_api_client_jwt(
            self.user,
            secret=self.secret,
            aud=aud,
            additional_claims=additional_claims,
        )
