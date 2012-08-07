from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    users = models.ManyToManyField(User, related_name="roles")

    def __unicode__(self):
        return self.name

    @staticmethod
    def register(name):
        return Role.objects.get_or_create(name=name)[0]

    def register_permissions(self, permissions):
        for p in permissions:
            if not self.permissions.filter(name=p):
                self.permissions.add(Permission.register(p))

    def inherit_permissions(self, role):
        self.register_permissions(map(lambda p: p.name, role.permissions.all()))


class Permission(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    users = models.ManyToManyField(User, related_name="permissions")
    roles = models.ManyToManyField(Role, related_name="permissions")

    def __unicode__(self):
        return self.name

    @staticmethod
    def register(name):
        return Permission.objects.get_or_create(name=name)[0]

