import json

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from api_manager.models import GroupProfile, Organization

class Command(BaseCommand):
    """
    Migrates legacy organization data and user relationships from older Group model approach to newer concrete Organization model
    """

    def handle(self, *args, **options):

        org_groups = GroupProfile.objects.filter(group_type='organization')

        for org in org_groups:
            data = json.loads(org.data)
            migrated_org = Organization.objects.create(
                name=data['name'],
                display_name=data['display_name'],
                contact_name=data['contact_name'],
                contact_email=data['contact_email'],
                contact_phone=data['contact_phone']
            )
            group = Group.objects.get(groupprofile=org.id)
            users = group.user_set.all()
            for user in users:
                migrated_org.users.add(user)
            linked_groups = group.grouprelationship.get_linked_group_relationships()
            for linked_group in linked_groups:
                if linked_group.to_group_relationship_id is not org.id: # Don't need to carry the symmetrical component
                    actual_group = Group.objects.get(id=linked_group.to_group_relationship_id)
                    migrated_org.groups.add(actual_group)
