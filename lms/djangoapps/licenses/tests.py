import logging
from uuid import uuid4
from random import shuffle
from tempfile import NamedTemporaryFile

from django.test import TestCase
from django.core.management import call_command

from models import CourseSoftware, UserLicense

COURSE_1 = 'MITx/6.002x/2012_Fall'

SOFTWARE_1 = 'matlab'
SOFTWARE_2 = 'stata'

log = logging.getLogger(__name__)


class CommandTest(TestCase):
    def test_import_serial_numbers(self):
        size = 20

        log.debug('Adding one set of serials for {0}'.format(SOFTWARE_1))
        with generate_serials_file(size) as temp_file:
            args = [COURSE_1, SOFTWARE_1, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('Adding one set of serials for {0}'.format(SOFTWARE_2))
        with generate_serials_file(size) as temp_file:
            args = [COURSE_1, SOFTWARE_2, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('There should be only 2 course-software entries')
        software_count = CourseSoftware.objects.all().count()
        self.assertEqual(2, software_count)

        log.debug('We added two sets of {0} serials'.format(size))
        licenses_count = UserLicense.objects.all().count()
        self.assertEqual(2 * size, licenses_count)

        log.debug('Adding more serial numbers to {0}'.format(SOFTWARE_1))
        with generate_serials_file(size) as temp_file:
            args = [COURSE_1, SOFTWARE_1, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('There should be still only 2 course-software entries')
        software_count = CourseSoftware.objects.all().count()
        self.assertEqual(2, software_count)

        log.debug('Now we should have 3 sets of 20 serials'.format(size))
        licenses_count = UserLicense.objects.all().count()
        self.assertEqual(3 * size, licenses_count)

        cs = CourseSoftware.objects.get(pk=1)

        lics = UserLicense.objects.filter(software=cs)[:size]
        known_serials = list(l.serial for l in lics)
        known_serials.extend(generate_serials(10))

        shuffle(known_serials)

        log.debug('Adding some new and old serials to {0}'.format(SOFTWARE_1))
        with NamedTemporaryFile() as f:
            f.write('\n'.join(known_serials))
            f.flush()
            args = [COURSE_1, SOFTWARE_1, f.name]
            call_command('import_serial_numbers', *args)

        log.debug('Check if we added only the new ones')
        licenses_count = UserLicense.objects.filter(software=cs).count()
        self.assertEqual((2 * size) + 10, licenses_count)


def generate_serials(size=20):
    return [str(uuid4()) for _ in range(size)]


def generate_serials_file(size=20):
    serials = generate_serials(size)

    temp_file = NamedTemporaryFile()
    temp_file.write('\n'.join(serials))
    temp_file.flush()

    return temp_file
