"""
Management command to sync platform users with hubspot
./manage.py lms sync_hubspot_contacts
./manage.py lms sync_hubspot_contacts --initial-sync-days=7 --batch-size=20
"""
import itertools
import json
import traceback
import urlparse
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.html import escapejs

from edx_rest_api_client.client import EdxRestApiClient
from slumber.exceptions import HttpClientError, HttpServerError

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from student.models import UserAttribute, UserProfile
from util.query import use_read_replica_if_available


HUBSPOT_API_BASE_URL = 'https://api.hubapi.com'


class Command(BaseCommand):
    """
    Command to create contacts in hubspot for those partner who has enabled hubspot integration.
    This command is suppose to sync contact with hubspot on daily basis.
    """

    def _get_hubspot_enabled_sites(self):
        """
        Returns: list of site configurations having hubspot integration enabled
        """
        site_confs = SiteConfiguration.objects.all()
        hubspot_sites = [
            site_conf for site_conf in site_confs
            if site_conf.get_value('HUBSPOT_API_KEY')
        ]
        return hubspot_sites

    def _get_last_synced_contact_email(self, site_conf):
        """
        Returns: last synced contact email for given site

        """
        api_key = site_conf.get_value('HUBSPOT_API_KEY')
        last_contact_email = None
        client = EdxRestApiClient(urlparse.urljoin(HUBSPOT_API_BASE_URL, 'contacts/v1/lists/all/contacts'))
        try:
            response = client.recent.get(hapikey=api_key, count=1, property='email')
            if 'contacts' in response:
                for contact in response['contacts']:
                    last_contact_email = contact.get('properties').get('email').get('value')

        except (HttpClientError, HttpServerError) as ex:
            message = u'An error occurred while getting recent contact for site {domain}, {message}'.format(
                domain=site_conf.site.domain, message=ex.message
            )
            self.stderr.write(message)
        return last_contact_email

    def _get_unsynced_users(self, site_domain, last_synced_user, days_threshold):
        """
        Args:
            site_domain: site where we need unsynced users
            last_synced_user: last synced user
            days_threshold: number of days threshold to sync users in case we don't have last synced user

        Returns: Ordered list of users needs to be synced

        """
        if last_synced_user:
            self.stdout.write(
                u'Started pulling unsynced contacts for site {site} created after user {user}'.format(
                    site=site_domain, user=last_synced_user
                )
            )
            users = User.objects.select_related('profile').filter(id__gt=last_synced_user.id).order_by('pk')
        else:
            # If we don't have last synced user get all users who joined on between today and threshold days ago
            start_date = datetime.now().date() - timedelta(days_threshold)
            self.stdout.write(
                u'Started pulling unsynced contacts for site {site} from {start_date}'.format(
                    site=site_domain, start_date=start_date
                )
            )
            users = User.objects.select_related('profile').filter(date_joined__date__gte=start_date).order_by('pk')

        for user in use_read_replica_if_available(users):
            if UserAttribute.get_user_attribute(user, 'created_on_site') == site_domain:
                yield user

    def _get_level_of_education_display(self, loe):
        """
        Returns: Descriptive level of education
        """
        level_of_education = ''
        for _loe in UserProfile.LEVEL_OF_EDUCATION_CHOICES:
            if loe == _loe[0]:
                level_of_education = _loe[1]
        return level_of_education

    def _get_batched_users(self, users, batch_size=100):
        """
        Splits user's list into batches
        Args:
            users: users (generator) to be batched
            batch_size: size of batch
        """
        end = 0
        users_iter = iter(users)
        while True:
            users_batch = list(itertools.islice(users_iter, batch_size))
            if not users_batch:
                raise StopIteration
            start = end + 1
            end += len(users_batch)
            yield (start, end, users_batch)

    def _escape_json(self, value):
        """
        Escapes js for now. Additional escaping can be done here.
        """
        return escapejs(value)

    def _sync_with_hubspot(self, users_batch, site_conf):
        """
        Sync batch of users with hubspot
        """
        contacts = []
        for user in users_batch:
            if not hasattr(user, 'profile'):
                self.stdout.write(u'skipping user {} due to no profile found'.format(user))
                continue
            if not user.profile.meta:
                self.stdout.write(u'skipping user {} due to no profile meta found'.format(user))
                continue
            meta = json.loads(user.profile.meta)
            contact = {
                "email": user.email,
                "properties": [
                    {
                        "property": "firstname",
                        "value": self._escape_json(meta.get('first_name', ''))
                    },
                    {
                        "property": "lastname",
                        "value": self._escape_json(meta.get('last_name', ''))
                    },
                    {
                        "property": "company",
                        "value": self._escape_json(meta.get('company', ''))
                    },
                    {
                        "property": "jobtitle",
                        "value": self._escape_json(meta.get('title', ''))
                    },
                    {
                        "property": "state",
                        "value": self._escape_json(meta.get('state', ''))
                    },
                    {
                        "property": "country",
                        "value": self._escape_json(meta.get('country', ''))
                    },
                    {
                        "property": "gender",
                        "value": self._escape_json(user.profile.gender)
                    },
                    {
                        "property": "degree",
                        "value": self._escape_json(
                            self._get_level_of_education_display(user.profile.level_of_education)
                        )
                    },
                ]
            }
            contacts.append(contact)

        api_key = site_conf.get_value('HUBSPOT_API_KEY')
        client = EdxRestApiClient(urlparse.urljoin(HUBSPOT_API_BASE_URL, 'contacts/v1/contact'))
        try:
            client.batch.post(contacts, hapikey=api_key)
            return len(contacts)
        except (HttpClientError, HttpServerError) as ex:
            message = u'An error occurred while syncing batch of contacts for site {domain}, {message}'.format(
                domain=site_conf.site.domain, message=ex.message
            )
            self.stderr.write(message)
            return 0

    def add_arguments(self, parser):
        """
        Definition of arguments this command accepts
        """
        parser.add_argument(
            '--initial-sync-days',
            default=7,
            dest='initial_sync_days',
            type=int,
            help='Number of days before today to start initial sync',
        )
        parser.add_argument(
            '--batch-size',
            default=100,
            dest='batch_size',
            type=int,
            help='Size of contacts batch to be sent to hubspot',
        )

    def handle(self, *args, **options):
        """
        Main command handler
        """
        initial_sync_days = options['initial_sync_days']
        batch_size = options['batch_size']
        try:
            hubspot_sites = self._get_hubspot_enabled_sites()

            if not hubspot_sites:
                self.stdout.write(u'No hubspot enabled site found.')
                return

            for site_conf in hubspot_sites:
                successfully_synced_contacts = 0
                site_domain = site_conf.site.domain
                self.stdout.write(u'Syncing process started for site {site}'.format(site=site_domain))
                last_synced_user = None
                # get recently created contact to set a starting point for sync
                last_synced_contact_email = self._get_last_synced_contact_email(site_conf)
                if last_synced_contact_email:
                    self.stdout.write(
                        u'Last synced email: {email} for site {site}'.format(
                            email=last_synced_contact_email, site=site_domain
                        )
                    )

                    # get last synced contact from mysql database
                    last_synced_user = User.objects.filter(email=last_synced_contact_email).first()
                    if not last_synced_user:
                        self.stdout.write(
                            u'Failed to get user for last synced email {email} for site {site}'.format(
                                email=last_synced_contact_email, site=site_domain
                            )
                        )
                else:
                    self.stdout.write(
                        u'Last synced email: NOT FOUND for site {site}'.format(site=site_domain)
                    )

                site_unsynced_users = self._get_unsynced_users(site_domain, last_synced_user, initial_sync_days)

                for start, end, users_batch in self._get_batched_users(site_unsynced_users, batch_size):
                    self.stdout.write(
                        u'Syncing users batch from {start} to {end} unsynced contacts for site {site}'.format(
                            start=start, end=end, site=site_domain
                        )
                    )
                    successfully_synced_contacts += self._sync_with_hubspot(users_batch, site_conf)
                    self.stdout.write(
                        u'Successfully synced users batch from {start} to {end} for site {site}'.format(
                            start=start, end=end, site=site_domain
                        )
                    )

                self.stdout.write(
                    u'{count} contacts found and sycned for site {site}'.format(
                        count=successfully_synced_contacts, site=site_domain
                    )
                )

        except Exception as ex:
            traceback.print_exc()
            raise CommandError(u'Command failed with traceback %s' % str(ex))
