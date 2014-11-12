from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import json

from student.models import UserProfile


class Command(BaseCommand):
    help = """Extract full user information into a JSON file.
Pass a single filename."""

    def handle(self, *args, **options):
        file_output = open(args[0], 'w')
        users = User.objects.all()

        data_list = []
        for user in users:
            profile = UserProfile.objects.get(user=user)
            data = {
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'joined': user.date_joined.isoformat(),
                'name': profile.name,
                'language': profile.language,
                'location': profile.location,
            }
            data_list.append(data)
        json.dump(data_list, file_output)
        file_output.close()
