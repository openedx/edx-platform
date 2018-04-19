import json
from random import randint
from uuid import uuid4

from common.test.acceptance.fixtures import LMS_BASE_URL
from common.test.acceptance.fixtures.base import FixtureError, StudioApiFixture
from common.test.acceptance.fixtures.catalog import CatalogIntegrationMixin


class CourseEntitlementFixture(StudioApiFixture, CatalogIntegrationMixin):
    """
    Fixture for ensuring that a course entitlement exists.
    """

    def __init__(self, user, mode='verified', expired_at=None, enrollment_course_run=None):
        """
        Configure the course entitlement fixture to create an entitlement with

        `mode` `run` (both unicode).

        `expired_at` is a datetime object indicating the date on which the course entitlement became expired.
            The default is for the entitlement to be unexpired, which is generally what we want for testing
            so students can use the entitlement.
        """
        self._entitlement_dict = {
            'user': user,
            'course_uuid': str(uuid4()),
            'expired_at': expired_at,
            'mode': mode,
            'enrollment_course_run': enrollment_course_run,
            'order_number': randint(0, 999)
        }

    def __str__(self):
        """
        String representation of the course entitlement fixture, useful for debugging.
        """
        return "<CourseEntitlementFixture: course_uuid='{course_uuid}', mode='{mode}'>".format(**self._entitlement_dict)

    def install(self):
        """
        Create the course entitlement.
        This is NOT an idempotent method; if the entitlement already exists, this will
        raise a `FixtureError`.  You should use unique course identifiers to avoid
        conflicts between tests.
        """
        self._create_course_entitlement()
        return self

    def _create_course_entitlement(self):
        """
        Create the course entitlement described in the fixture.
        """
        # If the course entitlement already exists, this will respond
        # with a 200 and an error message, which we ignore.
        response = self.session.post(
            LMS_BASE_URL + '/api/entitlements/v1/entitlements/',
            data=json.dumps(self._entitlement_dict),
            headers=self.headers
        )

        try:
            err = response.json().get('ErrMsg')
        except ValueError:
            raise FixtureError(
                "Could not parse response from course entitlement request as JSON: '{0}'".format(
                    response.content))

        # This will occur if the course identifier is not unique
        if err is not None:
            raise FixtureError("Could not create course entitlement {0}.  Error message: '{1}'".format(self, err))

        if response.ok:
            self.entitlement_uuid = response.json()['uuid']
        else:
            raise FixtureError(
                "Could not create course entitlement {0}.  Status was {1}\nResponse content was: {2}".format(
                    self._entitlement_dict, response.status_code, response.content))

