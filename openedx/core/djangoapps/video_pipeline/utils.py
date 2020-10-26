"""
Utils for video_pipeline app.
"""
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user


def create_video_pipeline_api_client(user, api_client_id, api_client_secret, api_url):
    """
    Returns an API client which can be used to make Video Pipeline API requests.

    Arguments:
        user(User): A requesting user.
        api_client_id(unicode): Video pipeline client id.
        api_client_secret(unicode): Video pipeline client secret.
        api_url(unicode): It is video pipeline's API URL.
    """
    jwt_token = create_jwt_for_user(user, secret=api_client_secret, aud=api_client_id)
    return EdxRestApiClient(api_url, jwt=jwt_token)
