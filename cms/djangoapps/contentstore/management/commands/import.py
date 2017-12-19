"""
Script for importing courseware from XML format
"""
from django.core.management.base import BaseCommand

from django_comment_common.utils import are_permissions_roles_seeded, seed_permissions_roles
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_course_from_xml


class Command(BaseCommand):
    """
    Import the specified data directory into the default ModuleStore
    """
    help = 'Import the specified data directory into the default ModuleStore.'

    def add_arguments(self, parser):
        parser.add_argument('data_directory')
        parser.add_argument('course_dirs',
                            nargs='*',
                            metavar='course_dir')
        parser.add_argument('--nostatic',
                            action='store_true',
                            help='skip import of static content')

    def handle(self, *args, **options):
        data_dir = options['data_directory']
        do_import_static = not options['nostatic']
        source_dirs = options['course_dirs']
        if len(source_dirs) == 0:
            source_dirs = None

        self.stdout.write("Importing.  Data_dir={data}, source_dirs={courses}\n".format(
            data=data_dir,
            courses=source_dirs,
        ))
        mstore = modulestore()

        course_items = import_course_from_xml(
            mstore, ModuleStoreEnum.UserID.mgmt_command, data_dir, source_dirs, load_error_modules=False,
            static_content_store=contentstore(), verbose=True,
            do_import_static=do_import_static,
            create_if_not_present=True,
        )

        for course in course_items:
            course_id = course.id
            if not are_permissions_roles_seeded(course_id):
                self.stdout.write('Seeding forum roles for course {0}\n'.format(course_id))
                seed_permissions_roles(course_id)
