# -*- coding: utf-8 -*-
"""
Test the Groups REST API
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
import six

from student.tests.factories import UserFactory


class GroupsApiTestCase(APITestCase):
    """
    Test the groups API

    Per REST API test best practices, URLs are hard-coded (not using reverse),
    all data manipulation is done using the API, and tests won't break if new
    data fields are added to responses in a backwards-compatible way.
    """
    BASE_URL = '/api/groups/v1/groups/'

    def create_user_client(self, name="Alice", django_permissions=None, **kwargs):
        """
        Create a user and an HTTP client for testing
        """
        kwargs.setdefault("username", name.lower())
        kwargs.setdefault("first_name", name)
        kwargs.setdefault("last_name", "Tester")
        user = UserFactory.create(**kwargs)
        if django_permissions:
            content_type = ContentType.objects.get_for_model(Group)
            for codename in django_permissions:
                perm = Permission.objects.get(codename=codename, content_type=content_type)
                user.user_permissions.add(perm)
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    # Creating groups

    def _create_group(self, client, name, expect_status=status.HTTP_201_CREATED):
        """
        Helper method to create a group using the REST API
        """
        response = client.post(self.BASE_URL, {"name": name})
        self.assertEqual(response.status_code, expect_status)
        return response

    def test_create_group_no_permission(self):
        """
        A regular user does not have permission to create groups
        """
        client, _user = self.create_user_client()
        response = client.post(self.BASE_URL, {"name": "New Group"})
        self.assertEqual(response.status_code, 403)

    def test_create_group_with_permission(self):
        """
        A regular user can be granted permission to create groups
        """
        client, _user = self.create_user_client(django_permissions=['add_group'])
        response = client.post(self.BASE_URL, {"name": "New Group"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_group_staff(self):
        """
        Global staff users can create groups
        """
        client, _user = self.create_user_client(is_staff=True)
        response = client.post(self.BASE_URL, {"name": "New Group"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_group_bad_name(self):
        """
        Group names have to match certain requirements:
        """
        client, _user = self.create_user_client(is_staff=True)
        # Cannot contain '/' character (since group name goes in URLs sometimes)
        response = client.post(self.BASE_URL, {"name": "Illegal / Character"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Cannot be blank
        response = client.post(self.BASE_URL, {"name": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Cannot be the same as an existing name:
        response1 = client.post(self.BASE_URL, {"name": "SameName"})
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        response2 = client.post(self.BASE_URL, {"name": "SameName"})
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    # Listing groups

    def _list_groups(self, client):
        """
        Helper method to list groups using the REST API
        """
        response = client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [group["name"] for group in response.data]

    def test_list_groups(self):
        """
        Listing groups should only show groups that the user has permission to
        view (the user is a member, is a group admin, or is staff/superuser).
        """
        # Two regular users
        client_alex, _user = self.create_user_client("Alex")
        client_jamie, _user = self.create_user_client("Jamie")
        # A regular user with admin permission:
        client_admin, _user = self.create_user_client("Admin", django_permissions=['add_group'])

        # The "admin" user creates a new group:
        group_name = "Test Group"
        self._create_group(client_admin, group_name)
        # The admin user adds Alex to the group:
        self._add_user_to_group(client_admin, "alex", group_name)

        # Now Alex (group member, non-admin) can see the group:
        six.assertCountEqual(self, self._list_groups(client_alex), [group_name])
        # The admin user who created the group can see it:
        six.assertCountEqual(self, self._list_groups(client_admin), [group_name])
        # But Jamie (regular user, not a group member) cannot:
        six.assertCountEqual(self, self._list_groups(client_jamie), [])

    # Group details / member lists

    def _get_group_details(self, client, group_name, expect_status=status.HTTP_200_OK):
        """
        Helper method to get details of a group using the REST API
        """
        response = client.get(self.BASE_URL + group_name + "/")
        self.assertEqual(response.status_code, expect_status)
        return response.data

    def test_cannot_see_groups_without_permission(self):
        """
        Test that users without permission cannot see a group
        """
        client_creator, _user = self.create_user_client("GroupCreator", django_permissions=['add_group'])
        client_other, _user = self.create_user_client("Other")
        group_name = "Test Group"
        self._create_group(client_creator, group_name)
        # The creator can now see the group:
        self._get_group_details(client_creator, group_name)
        # The other user cannot see the new group:
        self._get_group_details(client_other, group_name, expect_status=status.HTTP_404_NOT_FOUND)
        # Nor can the other user see a group that doesn't exist:
        self._get_group_details(client_other, "FakeGroup", expect_status=status.HTTP_404_NOT_FOUND)

    def test_see_group_members(self):
        """
        See the members and admins of a group
        """
        client_creator, _user = self.create_user_client("GroupCreator", django_permissions=['add_group'])
        client_member1, _user = self.create_user_client("Member1")
        _client_member2, _user = self.create_user_client("Member2")
        group_name = "Test Group"
        self._create_group(client_creator, group_name)
        self._add_user_to_group(client_creator, "member1", group_name)
        self._add_user_to_group(client_creator, "member2", group_name)
        # Now the creator can see the group details:
        details = self._get_group_details(client_creator, group_name)
        self.assertEqual(details["name"], group_name)
        self.assertEqual(len(details["users"]), 2)  # 2 members. The admin is not a member.
        six.assertCountEqual(
            self,
            [(u["username"], u["name"]) for u in details["users"]],
            [("member1", "Member1 Tester"), ("member2", "Member2 Tester")],
        )
        self.assertEqual(len(details["admins"]), 1)
        self.assertEqual(details["admins"][0]["username"], "groupcreator")
        self.assertEqual(details["admins"][0]["name"], "GroupCreator Tester")
        # The members can also see the same data
        details_member1 = self._get_group_details(client_member1, group_name)
        self.assertEqual(details, details_member1)

    # Changing group membership

    def _add_user_to_group(self, client, username, group_name, mode="user", expect_status=status.HTTP_204_NO_CONTENT):
        """
        Helper method to add a user to a group using the REST API
        """
        response = client.put(self.BASE_URL + group_name + "/" + mode + "/" + username + "/")
        self.assertEqual(response.status_code, expect_status)
        return response

    def _remove_user_from_group(
        self, client, username, group_name, mode="user", expect_status=status.HTTP_204_NO_CONTENT,
    ):
        """
        Helper method to remove a user from a group using the REST API
        """
        response = client.delete(self.BASE_URL + group_name + "/" + mode + "/" + username + "/")
        self.assertEqual(response.status_code, expect_status)
        return response

    def test_change_membership(self):
        """
        Test adding/removing users and admins from the group
        """
        # Two regular users
        client_alex, _user = self.create_user_client("Alex")
        client_jamie, _user = self.create_user_client("Jamie")
        # A regular user with admin permission:
        client_admin, _user = self.create_user_client("Admin", django_permissions=['add_group'])

        # The "admin" user creates a new group:
        group_name = "Test Group"
        self._create_group(client_admin, group_name)
        # The admin user adds Alex to the group:
        self._add_user_to_group(client_admin, "alex", group_name)

        # Verify that alex was added.
        details = self._get_group_details(client_admin, group_name)
        self.assertEqual(details["users"][0]["username"], "alex")

        # Neither Alex (group member, non admin) nor Jamie (not group member) should be able to add users to the group
        self._add_user_to_group(client_alex, "jamie", group_name, expect_status=status.HTTP_403_FORBIDDEN)
        # Since Jamie doesn't have even read permission, Jamie just gets a 404, not 403
        self._add_user_to_group(client_jamie, "jamie", group_name, expect_status=status.HTTP_404_NOT_FOUND)

        # Now also make alex an admin
        self.assertEqual(len(details["admins"]), 1)
        # Alex cannot make themself an admin:
        self._add_user_to_group(client_alex, "alex", group_name, mode="admin", expect_status=status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(details["admins"]), 1)
        # But the admin can make alex an admin:
        self._add_user_to_group(client_admin, "alex", group_name, mode="admin")
        details = self._get_group_details(client_admin, group_name)
        six.assertCountEqual(self, [u["username"] for u in details["admins"]], ["admin", "alex"])

        # Now remove Alex from the group but keep them as an admin:
        self._remove_user_from_group(client_admin, "alex", group_name)
        details = self._get_group_details(client_admin, group_name)
        self.assertEqual(len(details["users"]), 0)  # No users
        self.assertEqual(len(details["admins"]), 2)  # Alex and Admin are still admins

        # Removing an already removed user raises no error:
        self._remove_user_from_group(client_admin, "alex", group_name)

        # Now remove Alex as an admin:
        self._remove_user_from_group(client_admin, "alex", group_name, mode="admin")
        details = self._get_group_details(client_admin, group_name)
        self.assertEqual(len(details["users"]), 0)
        self.assertEqual(len(details["admins"]), 1)
        self.assertEqual(details["admins"][0]["username"], "admin")
