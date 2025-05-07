"""Module for v2 serializers."""

from cms.djangoapps.contentstore.rest_api.v2.serializers.downstreams import (
    ComponentLinksSerializer,
    PublishableEntityLinksSummarySerializer,
)
from cms.djangoapps.contentstore.rest_api.v2.serializers.home import CourseHomeTabSerializerV2

__all__ = [
    'CourseHomeTabSerializerV2',
    'ComponentLinksSerializer',
    'PublishableEntityLinksSummarySerializer',
]
