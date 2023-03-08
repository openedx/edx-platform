"""
A management command to update formus sites
"""
# pylint: disable=broad-except

import logging
import json

from wiki.models import URLPath
from wiki.core.exceptions import NoRootURL, MultipleRootURLs

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from openedx.features.edly.models import EdlySubOrganization
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Custom command to update forums sites
    Use this command to show updates
        python manage.py lms update_forums_sites
    Use this command to update database
        python manage.py lms update_forums_sites --apply
    """
    help = 'Update Forums Sites'

    def get_platfrom_name_from_site(self, lms_site):
        """
        Returns Platform Name from site configurations
        """
        try:
            conf = SiteConfiguration.objects.get(site=lms_site)
            return conf.site_values['DJANGO_SETTINGS_OVERRIDE']['PLATFORM_NAME']
        except Exception:
            return settings.PLATFORM_NAME

    def get_root(self, site):
        """
        Get root URLPath for a site
        """
        root_nodes = list(
            URLPath.objects.root_nodes().filter(site=site).select_related_common()
        )
        # We fetch the nodes as a list and use len(), not count() because we need
        # to get the result out anyway. This only takes one sql query
        no_paths = len(root_nodes)
        if no_paths == 0:
            raise NoRootURL("You need to create a root article on site '%s'" % site)
        if no_paths > 1:
            raise MultipleRootURLs("Somehow you have multiple roots on %s" % site)
        return root_nodes[0]

    def get_or_create_root(self, site):
        """
        Returns the root article, or creates it if it doesn't exist.
        """
        try:
            root = self.get_root(site)
            if not root.article:
                root.delete()
                raise NoRootURL
            return root
        except NoRootURL:
            pass

        starting_content = "\n".join((
            _(u"Welcome to the {platform_name} Wiki").format(
                platform_name=self.get_platfrom_name_from_site(site),
            ),
            "===",
            _("Visit a course wiki to add an article."),
        ))

        root = URLPath.create_root(title="Wiki", site=site, content=starting_content)
        article = root.article
        article.group = None
        article.group_read = True
        article.group_write = False
        article.other_read = True
        article.other_write = False
        article.save()

        return root

    def add_arguments(self, parser):
        """
        Sending --apply argument with management command will also update the database,
        Otherwise It's generate report only.
        """
        parser.add_argument(
            '--apply',
            '-a',
            default=False,
            action='store_true',
            help='Update Database',
        )

    def update_forums_sites(self, apply=False):
        """
        Updates URLPaths based on EdlySubOrganizations
        Arguments:
            apply: Only update database when apply is set to True
        """
        updated_entries = {
            'SUCCESS': [],
            'FAILED': [],
            'UPDATED': [],
        }
        url_paths = URLPath.objects.filter(site__domain='example.com', parent__isnull=False)
        for url_path in url_paths:
            try:
                edx_org_slug = url_path.slug.split('.')[0]
                edly_org = EdlySubOrganization.objects.get(slug=edx_org_slug)
                updated_entries['SUCCESS'].append({
                    'id': url_path.id,
                    'slug': url_path.slug,
                    'partent_id': url_path.parent.id,
                    'site': str(url_path.site),
                })
                if apply:
                    parent_path = self.get_or_create_root(edly_org.lms_site)
                    url_path.parent = parent_path
                    url_path.site = edly_org.lms_site
                    url_path.save()
                    updated_entries['UPDATED'].append({
                        'id': url_path.id,
                        'slug': url_path.slug,
                        'partent_id': parent_path.id,
                        'site': str(edly_org.lms_site),
                    })
            except Exception as e:
                updated_entries['FAILED'].append({
                    'id': url_path.id,
                    'slug': url_path.slug,
                    'partent_id': url_path.parent.id,
                    'site': str(url_path.site),
                    'error': str(e),
                })
        logger.info(json.dumps(updated_entries, indent=4))
        if apply:
            logger.info("Entries Updated: {}/{}".format(
                len(updated_entries['UPDATED']), len(updated_entries['SUCCESS'])),
            )
            logger.info("Entries Not Applicable: {}".format(len(updated_entries['FAILED'])))
        else:
            logger.info("Database is not yet updated, send --apply flag with this command to update the database")

    def handle(self, *args, **options):
        apply = options.get('apply', False)
        self.update_forums_sites(apply)
