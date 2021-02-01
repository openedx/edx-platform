from factory.django import DjangoModelFactory  # lint-amnesty, pylint: disable=missing-module-docstring

from openedx.core.djangoapps.django_comment_common.models import Permission, Role


class RoleFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta(object):
        model = Role

    name = 'Student'
    course_id = 'edX/toy/2012_Fall'


class PermissionFactory(DjangoModelFactory):
    class Meta(object):
        model = Permission

    name = 'create_comment'
