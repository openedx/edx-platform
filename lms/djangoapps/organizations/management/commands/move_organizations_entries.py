__author__ = 'zia'
"""
One-time data migration script -- should not need to run it again
"""
import logging

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from organizations.models import Organization

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Moves existing organizations data from api_manager app to organizations app
    """
    help = "Command to move existing organizations from api_manager app to organizations app"

    def handle(self, *args, **options):
        existing_entries = Organization.objects.all().count()
        if existing_entries == 0:
            try:
                cursor = connection.cursor()
                cursor.execute('INSERT INTO organizations_organization SELECT * from api_manager_organization')
                log_msg = 'organizations entries moved from api_manager to organizations app'
                self.print_message(log_msg)

                cursor.execute('INSERT INTO organizations_organization_workgroups '
                               'SELECT * from api_manager_organization_workgroups')
                log_msg = 'organization_workgroups entries moved from api_manager to organizations app'
                self.print_message(log_msg)

                cursor.execute('INSERT INTO organizations_organization_users '
                               'SELECT * from api_manager_organization_users')
                log_msg = 'organization_users entries moved from api_manager to organizations app'
                self.print_message(log_msg)

                cursor.execute('INSERT INTO organizations_organization_groups '
                               'SELECT * from api_manager_organization_groups')
                log_msg = 'organization_groups entries moved from api_manager to organizations app'
                self.print_message(log_msg)
                transaction.commit()

            except Exception as e:
                log_msg = e.message
                self.print_message(log_msg)
        else:
            log_msg = 'oroganizations_organization is not empty. You might have already filled it.'
            self.print_message(log_msg)

    def print_message(self, msg):
        print msg
        log.info(msg)
