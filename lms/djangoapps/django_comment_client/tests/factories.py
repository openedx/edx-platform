from factory.django import DjangoModelFactory
from django_comment_common.models import Role, Permission


class RoleFactory(DjangoModelFactory):
    FACTORY_FOR = Role
    name = 'Student'
    course_id = 'edX/toy/2012_Fall'


class PermissionFactory(DjangoModelFactory):
    FACTORY_FOR = Permission
    name = 'create_comment'
