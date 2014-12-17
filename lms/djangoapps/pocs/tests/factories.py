from factory.django import DjangoModelFactory
from pocs.models import PersonalOnlineCourse
from pocs.models import PocMembership
from pocs.models import PocFutureMembership


class PocFactory(DjangoModelFactory):
    FACTORY_FOR = PersonalOnlineCourse
    display_name = "Test POC"


class PocMembershipFactory(DjangoModelFactory):
    FACTORY_FOR = PocMembership
    active = False


class PocFutureMembershipFactory(DjangoModelFactory):
    FACTORY_FOR = PocFutureMembership
