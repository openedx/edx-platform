"""Test the appsembler.eventtracking.tahoeusermetadata module."""

from copy import deepcopy
import factory
import json
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

TAHOE_USER_METADATA_CONTEXT = {
    "tahoe_user_metadata": {
        "registration_extra": {"custom_reg_field": "value1"}
    }
}


class UserProfileWithMetadataFactory(UserProfileFactory):
    """Factory for UserProfile sequence with some tahoe_user_metadata."""

    def _meta_val(n):
        """Return a JSON meta value for Sequence member"""
        reg_field_value = "value{}".format(n % 2)
        meta_dict = {
            "tahoe_idp_metadata": {
                "registration_additional": {"custom_reg_field": reg_field_value}
            }
        } if n % 2 == 1 else {"tahoe_idp_metadata": {}}

        return json.dumps(meta_dict)

    meta = factory.Sequence(_meta_val)


class UserWithTahoeMetadataFactory(UserFactory):
    profile = factory.RelatedFactory(UserProfileWithMetadataFactory, 'user')


@pytest.fixture(autouse=True)
def users():
    return [UserWithTahoeMetadataFactory() for i in range(2)]


@pytest.fixture(autouse=True)
def base_event():
    return BASE_EVENT_WITH_CONTEXT


@pytest.fixture(autouse=True)
def processor():
    return TahoeUserMetadataProcessor()


@pytest.mark.django_db
def test_for_metadata_no_cache(users, base_event, processor):
    """Test happy path, Processor returns the event with user metadata in `context`."""
    event_with_metadata = deepcopy(base_event)
    event_with_metadata.update(context=TAHOE_USER_METADATA_CONTEXT)

    with patch(EVENTTRACKING_MODULE + '.tahoeusermetadata.get_current_user', MagicMock()) as mocked:
        mocked.return_value = users[1]
        event = processor(base_event)
        assert event == event_with_metadata


@pytest.mark.django_db
def test_no_context_added_if_no_metadata_of_interest(users, base_event, processor):
    """Test happy path, Processor returns the event with user metadata in `context`."""
    with patch(EVENTTRACKING_MODULE + '.tahoeusermetadata.get_current_user', MagicMock()) as mocked:
        mocked.return_value = users[0]
        event = processor(base_event)
        assert event == base_event


@pytest.mark.django_db
def test_get_user_from_db_when_not_avail_from_request(users, base_event, processor):
    event_with_metadata = deepcopy(base_event)
    event_with_metadata.update(context=TAHOE_USER_METADATA_CONTEXT)

    with patch(EVENTTRACKING_MODULE + '.tahoeusermetadata.get_current_user', MagicMock()) as mocked:
        mocked.return_value = None
        event_with_user_id = deepcopy(base_event)
        event_with_user_id.update({'user_id': users[1].id})
        event_with_metadata.update({'user_id': users[1].id})
        event = processor(event_with_user_id)
        assert event == event_with_metadata
