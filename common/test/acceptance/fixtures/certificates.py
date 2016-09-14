"""
Tools for creating certificates config fixture data.
"""

import json

from . import STUDIO_BASE_URL
from .base import StudioApiFixture


class CertificateConfigFixtureError(Exception):
    """
    Error occurred while installing certificate config fixture.
    """
    pass


class CertificateConfigUpdateFixtureError(Exception):
    """
    Error occurred while updating certificate config fixture.
    """
    pass


class CertificateConfigFixture(StudioApiFixture):
    """
    Fixture to create certificates configuration for a course
    """
    certificates = []

    def __init__(self, course_id, certificates_data):
        self.course_id = course_id
        self.certificates = certificates_data
        super(CertificateConfigFixture, self).__init__()

    def install(self):
        """
        Push the certificates config data to certificate endpoint.
        """
        response = self.session.post(
            '{}/certificates/{}'.format(STUDIO_BASE_URL, self.course_id),
            data=json.dumps(self.certificates),
            headers=self.headers
        )

        if not response.ok:
            raise CertificateConfigFixtureError(
                "Could not create certificate {0}.  Status was {1}".format(
                    json.dumps(self.certificates), response.status_code
                )
            )

        return self

    def update_certificate(self, certificate_id):
        """
        Update the certificates config data to certificate endpoint.
        """
        response = self.session.put(
            '{}/certificates/{}/{}'.format(STUDIO_BASE_URL, self.course_id, certificate_id),
            data=json.dumps(self.certificates),
            headers=self.headers
        )

        if not response.ok:
            raise CertificateConfigUpdateFixtureError(
                "Could not update certificate {0}.  Status was {1}".format(
                    json.dumps(self.certificates), response.status_code
                )
            )

        return self
