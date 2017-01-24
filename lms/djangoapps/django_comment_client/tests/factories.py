from factory.django import DjangoModelFactory
from django_comment_common.models import Role, Permission


class RoleFactory(DjangoModelFactory):
    class Meta(object):
        model = Role

    name = 'Student'
    course_id = 'edX/toy/2012_Fall'


class PermissionFactory(DjangoModelFactory):
    class Meta(object):
        model = Permission

    name = 'create_comment'
