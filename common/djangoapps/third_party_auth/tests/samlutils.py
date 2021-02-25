"""
Utility functions for use in SAMLProviderConfig, SAMLProviderData tests
"""

from edx_rest_framework_extensions.auth.jwt.cookies import jwt_cookie_name
from edx_rest_framework_extensions.auth.jwt.tests.utils import generate_jwt_token, generate_unversioned_payload


def _jwt_token_from_role_context_pairs(user, role_context_pairs):
    """
    Generates a new JWT token with roles assigned from pairs of (role name, context).
    """
    roles = []
    for role, context in role_context_pairs:
        role_data = f'{role}'
        if context is not None:
            role_data += f':{context}'
        roles.append(role_data)

    payload = generate_unversioned_payload(user)
    payload.update({'roles': roles})
    return generate_jwt_token(payload)


def set_jwt_cookie(client, user, role_context_pairs=None):
    """
    Set jwt token in cookies
    """
    jwt_token = _jwt_token_from_role_context_pairs(user, role_context_pairs or [])
    client.cookies[jwt_cookie_name()] = jwt_token
