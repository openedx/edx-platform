"""
TODO (ARCH-248)
Deprecated JwtBuilder class.
Use openedx.core.djangoapps.oauth_dispatch.jwt.JwtBuilder directly.
This is here for backward compatibility reasons only.
"""
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user


class JwtBuilder(object):
    """
    Deprecated. See module docstring above.
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
        Deprecated. See module docstring above.
        """
        return create_jwt_for_user(
            self.user,
            secret=self.secret,
            aud=aud,
            additional_claims=additional_claims,
        )
