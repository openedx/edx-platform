"""Test the appsembler.eventtracking.tahoeusermetadata module."""

import factory
from mock import MagicMock, patch
import pytest

from openedx.core.djangoapps.appsembler.eventtracking.tahoeusermetadata import (
    TahoeUserMetadataProcessor,
    # TahoeUserProfileMetadataCache
)
from student.tests.factories import UserFactory, UserProfileFactory


EVENTTRACKING_MODULE = 'openedx.core.djangoapps.appsembler.eventtracking'

BASE_EVENT_WITH_CONTEXT = {
    "name": "event_name",
    "time": "2022-08-29T15:42:50.636766+00:00",
    "context": {},
    "data": {}
}


class UserProfileWithMetadataFactory(UserProfileFactory):

    meta = factory.Sequence(lambda n: {
        "tahoe_user_metadata": {
            "some_other_key": "some_other_val",
            "registration_extra": {"custom_reg_field": "value{n}"}
        }
    } if n == 1 else {"tahoe_user_metadata": {}}
    )


class UserWithTahoeMetadataFactory(UserFactory):
    profile = factory.RelatedFactory(UserProfileWithMetadataFactory, 'user')


@pytest.mark.django_db
class TahoeUserMetadataProcessorTests():
    """"""
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create Users and UserProfiles to test with."""
        self.users = [UserWithTahoeMetadataFactory() for i in range(1, 2)]
        self.base_event = BASE_EVENT_WITH_CONTEXT
        self.processor = TahoeUserMetadataProcessor()

    @patch(EVENTTRACKING_MODULE + '.tahoeusermetadata.get_current_user', MagicMock())
    def test_for_metadata_no_cache(self, mocked_get_current_user):
        """Test happy path, Processor returns the event with user metadata in `context`."""
        mocked_get_current_user.return_value = self.users[0]
        expected = BASE_EVENT_WITH_CONTEXT.update(context={
            "tahoe_user_metadata": {
                "some_other_key": "some_other_val",
                "registration_extra": {"custom_reg_field": "value1"}
            }
        })
        event = self.processor(self.base_event)
        assert event == expected
