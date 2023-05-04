from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus.models import Student
from openedx.features.genplus_features.genplus.constants import SchoolTypes

class Command(BaseCommand):
    help = 'Fetch SCN number for students from RMUnify'

    def handle(self, *args, **options):
        rm_unify = RmUnify()
        for student in Student.objects.filter(gen_user__school__type=SchoolTypes.RM_UNIFY):
            if student.gen_user.identity_guid:
                url = f'https://api.platform.rmunify.com/graph/organisation/{student.gen_user.school.guid}/student/{student.gen_user.identity_guid}'
                response = rm_unify.fetch(url)
                if response:
                    try:
                        student.scn = response['ScottishCandidateNumber']
                        student.save()
                        self.stdout.write(self.style.SUCCESS(f'SCN updated for {student.gen_user.email}'))
                    except KeyError:
                        self.stdout.write(self.style.ERROR(f'SCN not found for {student.gen_user.email}'))
        self.stdout.write(self.style.SUCCESS('DONE!!'))
