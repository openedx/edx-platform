"""
Command module to synchronize users with NodeBB
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Synchronizes users on Open edX with those present on NodeBB. Pushes any unpushed profile changes to NodeBB'

    def handle(self, **options):
        print "hello world"
