from factory.django import DjangoModelFactory

from openedx.features.badging.models import Badge, UserBadge


class BadgeFactory(DjangoModelFactory):
    class Meta(object):
        model = Badge

    description = "This is a sample badge"
    image = "path/to/image"


class UserBadgeFactory(DjangoModelFactory):
    class Meta(object):
        model = UserBadge

    course_id = ""
    community_id = -1
