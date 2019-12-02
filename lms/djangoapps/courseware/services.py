"""
Courseware services.
"""
from __future__ import absolute_import

import json

from lms.djangoapps.courseware.models import StudentModule


class UserStateService(object):
    """
    User state service to make state accessible in runtime.
    """

    def get_state_as_dict(self, username, block_id):
        """
        Return dict containing user state for a given set of parameters.

        Arguments:
            username: username of the user for whom the data is being retrieved
            block_id: string/object representation of the block whose user state is required

        Returns:
            Returns a dict containing user state, if present, else empty.
        """
        try:
            student_module = StudentModule.objects.get(
                student__username=username,
                module_state_key=block_id
            )
            return json.loads(student_module.state)
        except StudentModule.DoesNotExist:
            return {}
