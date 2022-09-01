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


@pytest.fixture(autouse=True)
def users():
    return [UserWithTahoeMetadataFactory() for i in range(1, 2)]


@pytest.fixture(autouse=True)
def base_event():
    return BASE_EVENT_WITH_CONTEXT


@pytest.fixture(autouse=True)
def processor():
    return TahoeUserMetadataProcessor()


@pytest.mark.django_db
def test_for_metadata_no_cache(users, base_event, processor):
    """Test happy path, Processor returns the event with user metadata in `context`."""
    with patch(EVENTTRACKING_MODULE + '.tahoeusermetadata.get_current_user', MagicMock()) as mocked:
        mocked.return_value = users[0]
        base_event.update(context={
            "tahoe_user_metadata": {
                "some_other_key": "some_other_val",
                "registration_extra": {"custom_reg_field": "value1"}
            }
        })
        event = processor(base_event)
        assert event == base_event
