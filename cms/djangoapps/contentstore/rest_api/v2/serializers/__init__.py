"""Module for v2 serializers."""

from cms.djangoapps.contentstore.rest_api.v2.serializers.downstreams import (
    PublishableEntityLinksSerializer,
    PublishableEntityLinksSummarySerializer,
)
from cms.djangoapps.contentstore.rest_api.v2.serializers.home import CourseHomeTabSerializerV2

__all__ = [
    'CourseHomeTabSerializerV2',
    'PublishableEntityLinksSerializer',
    'PublishableEntityLinksSummarySerializer',
]
