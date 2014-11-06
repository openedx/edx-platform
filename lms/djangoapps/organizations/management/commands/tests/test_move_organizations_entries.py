import mock
from django.test import TestCase
from django.db import connection, transaction, models
from organizations.management.commands import move_organizations_entries
from organizations.models import Organization
from student.tests.factories import UserFactory, GroupFactory
from django.contrib.auth.models import Group, User
from projects.models import Workgroup, Project
from model_utils.models import TimeStampedModel
from south.db import db

class MoveOrganizationEntriesTests(TestCase):
    """
    Test suite for organization table data copy from api_manager to organizations
    """
    def setUp(self):

        # Create tables and add data
        user1 = UserFactory()
        user2 = UserFactory()
        group1 = GroupFactory()
        group2 = GroupFactory()
        proj = Project()
        proj.course_id = 'slashes:test+cs234+ct323'
        proj.content_id = 'location:test+cs234+ct323+chapter+b145cc8196734885ac8835b841d486ee'
        proj.save()
        workgroup = Workgroup()
        workgroup.name = 'Test workgroup'
        workgroup.project = proj
        workgroup.save()

        for i in xrange(1, 9):
            org = self.organization()
            org.name = 'test_and_company {}'.format(i)
            org.display_name = 'test display name {}'.format(i)
            org.contact_name = 'test contact name {}'.format(i)
            org.contact_email = 'test{}@test.com'.format(i)
            org.save()
            org.users.add(user1, user2)
            org.groups.add(group1, group2)
            org.workgroups.add(workgroup)


    def test_organization_entries_copy(self):
        """
        Test organization entries copy from api_manager app to organizations app
        """
        # Run the command
        move_organizations_entries.Command().handle()
        total_orgs_old = self.organization.objects.all().count()
        total_orgs_new = Organization.objects.all().count()
        self.assertEqual(total_orgs_old, total_orgs_new)

        total_org_users_old = 0
        total_org_users_new = 0
        for org in self.organization.objects.all():
            total_org_users_old += org.users.all().count()

        for org in Organization.objects.all():
            total_org_users_new += org.users.all().count()
        self.assertEqual(total_org_users_old, total_org_users_new)

        total_org_groups_old = 0
        total_org_groups_new = 0
        for org in self.organization.objects.all():
            total_org_groups_old += org.groups.all().count()

        for org in Organization.objects.all():
            total_org_groups_new += org.groups.all().count()
        self.assertEqual(total_org_groups_old, total_org_groups_new)

        total_org_workgroups_old = 0
        total_org_workgroups_new = 0
        for org in self.organization.objects.all():
            total_org_workgroups_old += org.workgroups.all().count()

        for org in Organization.objects.all():
            total_org_workgroups_new += org.workgroups.all().count()
        self.assertEqual(total_org_workgroups_old, total_org_workgroups_new)
