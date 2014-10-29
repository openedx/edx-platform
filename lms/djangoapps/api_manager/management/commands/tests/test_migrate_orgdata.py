"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
import json
import uuid

from django.contrib.auth.models import Group, User
from django.test import TestCase

from api_manager.management.commands import migrate_orgdata
from api_manager.models import GroupProfile, GroupRelationship
from organizations.models import Organization


class MigrateOrgDataTests(TestCase):
    """
    Test suite for data migration script
    """

    def test_migrate_orgdata(self):
        """
        Test the data migration
        """

        # Create some old-style Group organizations to migrate
        group_name = str(uuid.uuid4())
        group_type = "organization"
        groupdata = {}
        groupdata['name'] = "Group 1 Data Name"
        groupdata['display_name'] = "Group 1 Data Display Name"
        groupdata['contact_name'] = "Group 1 Data Contact Name"
        groupdata['contact_email'] = "Group 1 Data Contact Email"
        groupdata['contact_phone'] = "Group 1 Data Contact Phone"
        group = Group.objects.create(name=group_name)
        GroupRelationship.objects.create(group_id=group.id)
        GroupProfile.objects.get_or_create(
            group_id=group.id,
            group_type=group_type,
            name=groupdata['name'],
            data=json.dumps(groupdata)
        )
        user = User.objects.create(email='user1@edx.org', username='user1', password='user1')
        group.user_set.add(user)
        linked_group = Group.objects.create(name='Group 1 Linked Group')
        linked_group_relationship = GroupRelationship.objects.create(group_id=linked_group.id)
        group.grouprelationship.add_linked_group_relationship(linked_group_relationship)

        group2_name = str(uuid.uuid4())
        group2_type = "organization"
        groupdata = {}
        groupdata['name'] = "Group 2 Data Name"
        groupdata['display_name'] = "Group 2 Data Display Name"
        groupdata['contact_name'] = "Group 2 Data Contact Name"
        groupdata['contact_email'] = "Group 2 Data Contact Email"
        groupdata['contact_phone'] = "Group 2 Data Contact Phone"
        group2 = Group.objects.create(name=group2_name)
        GroupRelationship.objects.create(group_id=group2.id)
        GroupProfile.objects.get_or_create(
            group_id=group2.id,
            group_type=group2_type,
            name=groupdata['name'],
            data=json.dumps(groupdata)
        )
        user2 = User.objects.create(email='user2@edx.org', username='user2', password='user2')
        group2.user_set.add(user2)
        linked_group2 = Group.objects.create(name='Group 2 Linked Group')
        linked_group2_relationship = GroupRelationship.objects.create(group_id=linked_group2.id)
        group2.grouprelationship.add_linked_group_relationship(linked_group2_relationship)

        # Run the data migration
        migrate_orgdata.Command().handle()

        # Confirm that the data has been properly migrated
        organizations = Organization.objects.all()
        for org in organizations:
            self.assertEqual('Group {} Data Name'.format(org.id), org.name)
            self.assertEqual('Group {} Data Display Name'.format(org.id), org.display_name)
            self.assertEqual('Group {} Data Contact Name'.format(org.id), org.contact_name)
            self.assertEqual('Group {} Data Contact Email'.format(org.id), org.contact_email)
            self.assertEqual('Group {} Data Contact Phone'.format(org.id), org.contact_phone)

            for user in org.users.all():
                self.assertEqual('user{}@edx.org'.format(user.id), user.email)
                self.assertEqual('user{}'.format(user.id), user.username)

            for group in org.groups.all():
                self.assertEqual('Group {} Linked Group'.format(org.id), group.name)
