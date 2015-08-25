"""
One-time data migration script -- shoulen't need to run it again
"""
import json

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from api_manager.models import GroupProfile
from organizations.models import Organization


class Command(BaseCommand):
    """
    Migrates legacy organization data and user relationships from older Group model approach to newer concrete Organization model
    """

    def handle(self, *args, **options):

        org_groups = GroupProfile.objects.filter(group_type='organization')

        for org in org_groups:
            data = json.loads(org.data)

            name = org.name
            display_name = data.get('display_name', name)
            contact_name = data.get('contact_name', None)
            contact_email = data.get('email', None)
            if contact_email is None:
                contact_email = data.get('contact_email', None)
            contact_phone = data.get('phone', None)
            if contact_phone is None:
                contact_phone = data.get('contact_phone', None)

            migrated_org = Organization.objects.create(
                name=name,
                display_name=display_name,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone
            )
            group = Group.objects.get(groupprofile=org.id)
            users = group.user_set.all()
            for user in users:
                migrated_org.users.add(user)
            linked_groups = group.grouprelationship.get_linked_group_relationships()
            for linked_group in linked_groups:
                if linked_group.to_group_relationship_id is not org.id:  # Don't need to carry the symmetrical component
                    actual_group = Group.objects.get(id=linked_group.to_group_relationship_id)
                    migrated_org.groups.add(actual_group)
