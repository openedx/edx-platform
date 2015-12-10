"""
Credentials service API views (v1).
"""
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.models import UserCredential, ProgramCertificate
from openedx.core.lib.api import parsers
from rest_framework import mixins, viewsets


class UserCredentialViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    """
    **Use Cases**

        List and update existing user credentials, and create new ones.

    **Example Requests**

        # Return a list of user credentials in the system.
        GET api/credentials/v1/users/

        If the request is successful, the HTTP status will be 200 and the response body will
        contain a JSON-formatted array of user credentials.

        # Create a new user credentials.
        POST api/credentials/v1/users/

        If the request is successful, the HTTP status will be 201 and the response body will
        contain a JSON-formatted representation of the newly-created user credentials.

        # Update existing user credentials.
        PATCH api/credentials/v1/users/{credential_id}

        If the request is successful, the HTTP status will be 200 and the response body will
        contain a JSON-formatted representation of the newly-updated user credentials.


    **Response Values**

        * id: The ID of the user credentials.
        * username: Username for whom certificate is created.
        * status: Current status of the certificate.
        * download_url: This will represent the pdf certificate url.
        * uuid: universal identifier for each credential.
        * created: The date/time this certificate was created.
        * modified: The date/time this certificate was last modified.
        * credential: It will represent the credential type from AbstractCredential model.

    """
    lookup_field = 'username'
    queryset = UserCredential.objects.all()
    serializer_class = serializers.UserCredentialSerializer
    parser_classes = (parsers.MergePatchParser,)

