"""
Script for importing courseware from XML format
"""


from django.core.management.base import BaseCommand

from openedx.core.djangoapps.django_comment_common.utils import are_permissions_roles_seeded, seed_permissions_roles
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.util.sandboxing import DEFAULT_PYTHON_LIB_FILENAME


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
                            help='Skip import of static content')
        parser.add_argument('--nopythonlib',
                            action='store_true',
                            help=(
                                'Skip import of course python library if it exists '
                                '(NOTE: If the static content import is not skipped, the python library '
                                'will be imported and this flag will be ignored)'
                            ))
        parser.add_argument('--python-lib-filename',
                            default=DEFAULT_PYTHON_LIB_FILENAME,
                            help='Filename of the course code library (if it exists)')

    def handle(self, *args, **options):
        data_dir = options['data_directory']
        source_dirs = options['course_dirs']
        if not source_dirs:
            source_dirs = None
        do_import_static = not options.get('nostatic', False)
        # If the static content is not skipped, the python lib should be imported regardless
        # of the 'nopythonlib' flag.
        do_import_python_lib = do_import_static or not options.get('nopythonlib', False)
        python_lib_filename = options.get('python_lib_filename')

        output = (
            u"Importing...\n"
            u"    data_dir={data}, source_dirs={courses}\n"
            u"    Importing static content? {import_static}\n"
            u"    Importing python lib? {import_python_lib}"
        ).format(
            data=data_dir,
            courses=source_dirs,
            import_static=do_import_static,
            import_python_lib=do_import_python_lib
        )
        self.stdout.write(output)
        mstore = modulestore()

        course_items = import_course_from_xml(
            mstore, ModuleStoreEnum.UserID.mgmt_command, data_dir, source_dirs, load_error_modules=False,
            static_content_store=contentstore(), verbose=True,
            do_import_static=do_import_static, do_import_python_lib=do_import_python_lib,
            create_if_not_present=True,
            python_lib_filename=python_lib_filename,
        )

        for course in course_items:
            course_id = course.id
            if not are_permissions_roles_seeded(course_id):
                self.stdout.write(u'Seeding forum roles for course {0}\n'.format(course_id))
                seed_permissions_roles(course_id)
