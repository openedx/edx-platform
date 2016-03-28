"""
Tools for creating grading config fixture data.
"""

import json

from . import STUDIO_BASE_URL
from .base import StudioApiFixture


class GradingConfigFixtureError(Exception):
    """
    Error occurred while installing grading config fixture.
    """
    pass


class GradingConfigFixture(StudioApiFixture):
    """
    Fixture to create grading configuration for a course
    """
    def __init__(self, course_id, grading_data):
        self.course_id = course_id
        self.grading_data = grading_data
        super(GradingConfigFixture, self).__init__()

    def install(self):
        """
        Configure course grading settings (e.g. grace_period, grade_cutoffs etc.)
        """
        url = '{}/settings/grading/{}'.format(STUDIO_BASE_URL, self.course_id)

        # First, get the current values
        response = self.session.get(url, headers=self.headers)

        if not response.ok:
            raise GradingConfigFixtureError(
                "Could not retrieve course grading settings.  Status was {0}".format(response.status_code)
            )

        try:
            grading_data = response.json()
        except ValueError:
            raise GradingConfigFixtureError(
                "Could not decode course grading settings as JSON: '{0}'".format(grading_data)
            )

        # Update the old grading_data with our overrides
        grading_data.update(self.grading_data)

        # POST the updated grading_data to Studio
        response = self.session.post(url, data=json.dumps(grading_data), headers=self.headers)

        if not response.ok:
            raise GradingConfigFixtureError(
                "Could not update course grading settings to '{0}' with {1}: Status was {2}.".format(
                    grading_data, url, response.status_code
                )
            )
