from datetime import tzinfo, timedelta, datetime

import json
import os
import pkg_resources
import socket

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ForeignKey
from django.db.models.fields.files import ImageFieldFile

from django_countries.fields import Country
from organizations.models import Organization


class ExtendedEncoder(DjangoJSONEncoder):
    def default(self, o, *args, **kwargs):
        if isinstance(o, ImageFieldFile):
            return str(o)
        if isinstance(o, Country):
            return o.code

        return super(ExtendedEncoder, self).default(o, *args, **kwargs)


class Command(BaseCommand):
    """
    Export a Tahoe website to be imported later.
    """
    # Increase this version by 1 after every backward-incompatible
    # change in the exported data format
    VERSION = 1

    def __init__(self, *args, **kwargs):
        self.debug = False
        self.version = self.VERSION
        self.default_path = os.getcwd()

        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            help='The domain of the organization to be deleted.',
            type=str,
        )
        parser.add_argument(
            '-o', '--output',
            help='The location you want to direct your output to.',
            default=self.default_path,
            type=str,
        )
        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            default=settings.DEBUG,
            help='Execute in debug mode (Will not commit or save changes).'
        )

    def handle(self, *args, **options):
        """
        Verifies the input and packs the site objects.
        """
        self.debug = options['debug']
        domain = options['domain']

        self.stdout.write('Inspecting project for potential problems...')
        self.check(display_num_errors=True)

        self.stdout.write(self.style.MIGRATE_HEADING('Exporting "%s" in progress...' % domain))
        site = self.get_site(domain)

        orgs = [org for org in Organization.objects.filter(sites__id=site.id)]

        # Processes the necessary data all exported objects share.
        # This data will be helpful if you are debugging or returning to an earlier state
        # later if any changes occur when packages gets updated, or our code changes.
        # Also some instance tracking information has been added.
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        export_data = {
            'version': self.version,
            'date': datetime.now(),
            'host_name': hostname,
            'ip_address': ip_address,
            'libraries': self.get_pip_packages(),
            'site_domain': site.domain,
            'objects': self.generate_objects(site, *orgs),
        }

        output = json.dumps(
            export_data,
            sort_keys=True,
            indent=1,
            cls=ExtendedEncoder
        )

        if self.debug:
            self.stdout.write('\nCommand output >>>')
            self.stdout.write(self.style.SQL_KEYWORD(output))

        path = self.generate_file_path(site, options['output'])
        self.write_to_file(path, output)

        self.stdout.write(self.style.SUCCESS('\nSuccessfully exported "%s" site' % site.domain))

    def get_site(self, site):
        """
        Locates the site to be exported and return its instance.

        :param site: The site of the site to be returned.
        :return: Returns the site object.
        """
        try:
            return Site.objects.get(domain=site)
        except Site.DoesNotExist:
            raise CommandError('Cannot find a site for the provided domain "%s"!' % site)

    def generate_objects(self, *args):
        """
        A Breadth First Search technique to extract the objects and processing its
        childern.
        What we are looking to achieve here is simply: Process the site; and
        any related object to it. This simply will give you all the data a site
        uses in order to operate properly when imported.

        We start with the site object, all discovered relations will be added
        to the queue to take part in the processing later. Same goes for any discovered
        relation.

        To avoid infinite loops and processing the same element more than one time, we check
        the discovered space (processing and processed objects) before adding new elements.

        :return: Simply all the discovered objects' data.
        """
        objects = []
        processing_queue = list(args)
        processed_objects = set()

        while processing_queue:
            instance = processing_queue.pop(0)
            item, pending_items = self.process_instance(instance)

            if item:
                objects.append(item)

            for pending_item in pending_items:
                if pending_item not in processed_objects and pending_item not in processing_queue:
                    processing_queue.append(pending_item)

            processed_objects.add(instance)

        return objects

    def process_instance(self, instance):
        """
        Inspired from: django.forms.models.model_to_dict
        Return a dict containing the data in ``instance`` suitable for passing as
        a Model's ``create`` keyword argument with all its discovered relations.
        """
        if not instance:
            return instance, []

        to_process = set()
        content_type = ContentType.objects.get_for_model(instance)
        opts = instance._meta  # pylint: disable=W0212

        data = {
            'model': '%s.%s' % (content_type.app_label, content_type.model),
            'fields': {},
        }

        if self.debug:
            self.stdout.write(self.style.MIGRATE_LABEL('Processing a %s object...' % data['model']))

        # We are going to iterate over the fields one by one, and depending
        # on the type, we determine how to process them.
        for field in opts.get_fields():
            if isinstance(field, ForeignKey):
                value, item = self._process_foreign_key(instance, field)
                data['fields'][field.name] = value
                to_process.add(item)

            elif field.one_to_many:
                items = self._process_one_to_many_relation(instance, field)
                to_process.update(items)

            elif field.one_to_one:
                items = self._process_one_to_one_relation(instance, field)
                to_process.update(items)

            elif field in opts.many_to_many:
                value, items = self._process_many_to_many_relation(instance, field)
                data['fields'][field.name] = value
                to_process.update(items)

            elif field in opts.concrete_fields or field in opts.private_fields:
                # Django stores the primary key under `id`
                if field.name == 'id':
                    data['pk'] = field.value_from_object(instance)
                else:
                    data['fields'][field.name] = field.value_from_object(instance)

        if self.debug:
            self.stdout.write('Finished processing %s object successfully!' % data['model'])
            self.stdout.write('%d new items to process' % len(to_process))
        else:
            self.stdout.write('.', ending='')

        return data, to_process

    def _process_foreign_key(self, instance, field):
        """
        What we are looking to achieve from here is the to get the ID of the object
        this instance is pointing at, and to return that instance for later processing.

        Note: This will process both; ForeignKeys and OneToOneKey. As in Django a
        OneToOneKey is sub class of ForeignKey.
        """
        # Gets the ID of the instance pointed at
        value = field.value_from_object(instance)
        return value, getattr(instance, field.name)

    def _process_one_to_many_relation(self, instance, field):
        """
        In OneToManyRelations, it is this model that other objects are pointing at.
        We are collecting these models to make sure that this we are not missing any
        data used in some apps, and to protect the organization integrity.

        Unlike ForeignKey, we just need too return the instances pointing at this
        object so we can process them later.
        """
        manager = getattr(instance, field.name, [])
        to_process = [obj for obj in manager.all()] if manager else []

        return to_process

    def _process_one_to_one_relation(self, instance, field):
        """
        This is a little bit similar to the OneToManyRel, except that we attribute
        returns one instance when called instead of a Model Manager.
        """
        try:
            obj = getattr(instance, field.name)
        except ObjectDoesNotExist:
            # Nothing to do, we didn't find any object related to this
            # in the other model.
            obj = None

        return [obj, ]

    def _process_many_to_many_relation(self, instance, field):
        """
        Exctrtacts all objects this instance is pointing at for later processing.
        Also returns a list of these objects IDs to be used as a value under the
        field name.
        """
        data = []
        to_process = []

        for relation in field.value_from_object(instance):
            data.append(relation.id)
            to_process.append(relation)

        return data, to_process

    def generate_file_path(self, site, output):
        """
        Determines and returns the output file name.
        If the user specified a full path, then just return it. If a partial path
        has been specified, we add the file name to it and return. Other wise, we
        combine our base path with the file name and return them.
        """
        base = output or self.default_path

        if base.endswith('.json'):
            return base

        now = datetime.now()
        timestamp = (now - datetime(1970, 1, 1)).total_seconds()

        file_name = '{}_{}.json'.format(site.name, timestamp)
        path = os.path.join(base, file_name)
        return path

    def get_pip_packages(self):
        """
        Returns a dictionary of pip packages names and their versions. Similar
        to `$ pip freeze`
        """
        return {
            package.project_name: package.version
            for package in pkg_resources.working_set
        }

    def write_to_file(self, path, content):
        """
        Writes content in the specified path.
        """

        with open(path, 'w') as file:
            file.write(content)

        self.stdout.write(self.style.SQL_KEYWORD('\nExported objects saved in %s' % path))
