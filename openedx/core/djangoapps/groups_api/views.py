"""
Implementation of a REST API for editing user groups
"""
# pylint: disable=abstract-method
from __future__ import absolute_import, division, print_function, unicode_literals

import bridgekeeper.rest_framework
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from openedx.core.djangoapps.groups_api.models import Group, User, GroupAdminUser
from openedx.core.lib.api.view_utils import standard_auth_classes


class GroupUserSerializer(serializers.Serializer):
    """
    Serializer for a user in a group
    """
    username = serializers.CharField(read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)


class GroupAdminUserSerializer(serializers.Serializer):
    """
    Serializer for an administrator in a group
    """
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)


class GroupSerializer(serializers.Serializer):
    """
    Serializer for a group of users
    """
    # ID is intentionally not exposed via the API; "name" is used instead.
    name = serializers.CharField(read_only=True)
    users = GroupUserSerializer(source="user_set", many=True, read_only=True)
    admins = GroupAdminUserSerializer(source="groupadminuser_set", many=True, read_only=True)


class SimpleGroupSerializer(serializers.Serializer):
    """
    Serializer for listing many groups of users
    """
    # ID is intentionally not exposed via the API; "name" is used instead.
    name = serializers.CharField(read_only=True)


class GroupCreationSerializer(serializers.Serializer):
    """
    Serializer for a new group of users
    """
    # Limit length of new names, and exclude '?', '/', and '#' characters
    name = serializers.RegexField('^[^/?#]+$', max_length=100)

    def create(self, validated_data):
        """ Create a new group """
        try:
            group = Group.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"name": "That name is already in use."})
        # The user who creates the group becomes the administrator
        group.groupadminuser_set.create(user=self.context['request'].user)
        return group


class DjangoAndBridgekeeperPermissions(permissions.DjangoObjectPermissions):
    """
    DRF permissions class that checks Bridgekeeper _and_ standard django
    permissions. This way, the general rules are defined using bridgekeeper, but
    exceptions can be granted to individual users or groups by granting them
    standard django permissions.
    """

    def has_permission(self, request, view):
        """
        Override has_permission so we only check object-level permissions
        """
        # For the create and list actions, we cannot apply per-object
        # permissions, so we check the generic permissions (note: the "list" can
        # still be filtered by permissions using RuleFilter).
        # For other actions, we _only_ want to check has_object_permission.
        # Otherwise, a user who doesn't have permission to edit groups in
        # general but does have permission to edit a specific group would be
        # disallowed from editing that specific group.
        if view.action in ('create', 'list'):
            return super(DjangoAndBridgekeeperPermissions, self).has_permission(request, view)
        return True  # Only check object-level permissions for this group.


class GroupViewSet(viewsets.ModelViewSet):
    """
    Viewset for Groups REST API
    """
    # The queryset.
    # Since the permissions checks do lookups on related models, distinct() is
    # needed to avoid duplicates, e.g. when a user is both a member and an admin
    queryset = Group.objects.all().distinct()
    serializer_class = GroupSerializer
    authentication_classes = standard_auth_classes
    permission_classes = (
        permissions.IsAuthenticated,
        DjangoAndBridgekeeperPermissions,
    )
    filter_backends = (bridgekeeper.rest_framework.RuleFilter, )
    pagination_class = None
    lookup_field = 'name'
    lookup_url_kwarg = 'group_name'

    def get_serializer_class(self):
        """ Get the serializer """
        # Use different serializers for some actions
        if self.action == 'create':
            return GroupCreationSerializer
        elif self.action == 'list':
            return SimpleGroupSerializer
        return super(GroupViewSet, self).get_serializer_class()

    @detail_route(methods=['put', 'delete'], url_path=r'user/(?P<username>[^/]+)')
    def change_user(self, request, group_name, username):  # pylint: disable=unused-argument
        """
        Add/remove a user in this group
        """
        # Permissions are enforced by get_object().
        # Generally, the group admins and global staff are the only ones allowed
        # to add/remove users.
        # Since this is a PUT/DELETE method, it uses the same checks as for
        # changing and deleting the group as a whole. With the bridgekeeper
        # permission rules, that will do the right thing.
        # One nuance is that users who are not group admins need the manual
        # 'delete group' permission in order to remove a user from any group.
        group = self.get_object()
        user = get_object_or_404(User, username=username)
        if request.method == 'PUT':
            try:
                group.user_set.add(user)
            except IntegrityError:
                pass  # user is already added.
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'DELETE':
            group.user_set.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValueError

    @detail_route(methods=['put', 'delete'], url_path=r'admin/(?P<username>[^/]+)')
    def change_admin(self, request, group_name, username):  # pylint: disable=unused-argument
        """
        Add/remove an admin user in this group

        Admins do not necessarily have to be members of the group.
        """
        # Permissions are the same as for change_user.
        group = self.get_object()
        user = get_object_or_404(User, username=username)
        if request.method == 'PUT':
            try:
                GroupAdminUser.objects.create(group=group, user=user)
            except IntegrityError:
                pass  # user is already added.
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'DELETE':
            try:
                GroupAdminUser.objects.get(group=group, user=user).delete()
            except GroupAdminUser.DoesNotExist:
                pass
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValueError
