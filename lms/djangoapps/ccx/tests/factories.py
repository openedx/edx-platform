from factory.django import DjangoModelFactory
from ccx.models import CustomCourseForEdX
from ccx.models import CcxMembership
from ccx.models import CcxFutureMembership


class CcxFactory(DjangoModelFactory):
    FACTORY_FOR = CustomCourseForEdX
    display_name = "Test CCX"


class CcxMembershipFactory(DjangoModelFactory):
    FACTORY_FOR = CcxMembership
    active = False


class CcxFutureMembershipFactory(DjangoModelFactory):
    FACTORY_FOR = CcxFutureMembership
