"""
Data models used for Blockstore API Client
"""

from datetime import datetime
from uuid import UUID

import attr
import six


def _convert_to_uuid(value):
    if not isinstance(value, UUID):
        return UUID(value)
    return value


@attr.s(frozen=True)
class Collection(object):
    """
    Metadata about a blockstore collection
    """
    uuid = attr.ib(type=UUID, converter=_convert_to_uuid)
    title = attr.ib(type=six.text_type)


@attr.s(frozen=True)
class Bundle(object):
    """
    Metadata about a blockstore bundle
    """
    uuid = attr.ib(type=UUID, converter=_convert_to_uuid)
    title = attr.ib(type=six.text_type)
    description = attr.ib(type=six.text_type)
    slug = attr.ib(type=six.text_type)
    drafts = attr.ib(type=dict)  # Dict of drafts, where keys are the draft names and values are draft UUIDs
    # Note that if latest_version is 0, it means that no versions yet exist
    latest_version = attr.ib(type=int, validator=attr.validators.instance_of(int))


@attr.s(frozen=True)
class Draft(object):
    """
    Metadata about a blockstore draft
    """
    uuid = attr.ib(type=UUID, converter=_convert_to_uuid)
    bundle_uuid = attr.ib(type=UUID, converter=_convert_to_uuid)
    name = attr.ib(type=six.text_type)
    updated_at = attr.ib(type=datetime, validator=attr.validators.instance_of(datetime))
    files = attr.ib(type=dict)
    links = attr.ib(type=dict)


@attr.s(frozen=True)
class BundleFile(object):
    """
    Metadata about a file in a blockstore bundle or draft.
    """
    path = attr.ib(type=six.text_type)
    size = attr.ib(type=int)
    url = attr.ib(type=six.text_type)
    hash_digest = attr.ib(type=six.text_type)


@attr.s(frozen=True)
class DraftFile(BundleFile):
    """
    Metadata about a file in a blockstore draft.
    """
    modified = attr.ib(type=bool)  # Was this file modified in the draft?


@attr.s(frozen=True)
class LinkReference(object):
    """
    A pointer to a specific BundleVersion
    """
    bundle_uuid = attr.ib(type=UUID, converter=_convert_to_uuid)
    version = attr.ib(type=int)
    snapshot_digest = attr.ib(type=six.text_type)


@attr.s(frozen=True)
class LinkDetails(object):
    """
    Details about a specific link in a BundleVersion or Draft
    """
    name = attr.ib(type=str)
    direct = attr.ib(type=LinkReference)
    indirect = attr.ib(type=list)  # List of LinkReference objects


@attr.s(frozen=True)
class DraftLinkDetails(LinkDetails):
    """
    Details about a specific link in a Draft
    """
    modified = attr.ib(type=bool)
