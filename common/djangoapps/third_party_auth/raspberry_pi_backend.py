from social_core.backends.oauth import BaseOAuth2
import logging
import jwt
from jwt import DecodeError, ExpiredSignatureError

logger = logging.getLogger(__name__)


class RaspberryPiOAuth2(BaseOAuth2):
    """Raspberry Pi Foundation OAuth authentication backend"""

    name = "custom-oauth2"
    AUTHORIZATION_URL = "https://auth-v1.raspberrypi.org/oauth2/auth"
    ACCESS_TOKEN_URL = "https://auth-v1.raspberrypi.org/oauth2/token"
    ACCESS_TOKEN_METHOD = "POST"
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ["openid", "email", "name", "force-consent"]
    authorize_params: {
        "brand": "edly",
    }

    def get_user_id(self, details, response):
        """Use subject (sub) claim as unique id."""
        return response.get("sub")

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get("response")
        id_token = response.get("id_token")

        try:
            return jwt.decode(
                id_token, audience="edly", options={"verify_signature": False}
            )
        except (DecodeError, ExpiredSignatureError) as error:
            logger("Error {error} while decoding id_token".format(error=error))

    def get_user_details(self, response):
        """Return user details from RPF account"""

        return {
            "username": response.get("nickname"),
            "email": response.get("email"),
            "fullname": response.get("name"),
        }
