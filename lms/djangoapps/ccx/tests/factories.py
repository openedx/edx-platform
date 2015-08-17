"""
Dummy factories for tests
"""
from factory.django import DjangoModelFactory
from ccx.models import CustomCourseForEdX  # pylint: disable=import-error
from ccx.models import CcxMembership  # pylint: disable=import-error
from ccx.models import CcxFutureMembership  # pylint: disable=import-error


class CcxFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    FACTORY_FOR = CustomCourseForEdX
    display_name = "Test CCX"
    id = None  # pylint: disable=redefined-builtin, invalid-name


class CcxMembershipFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    FACTORY_FOR = CcxMembership
    active = False


class CcxFutureMembershipFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    FACTORY_FOR = CcxFutureMembership
