from django.test import TestCase

from openedx.core.djangoapps.appsembler.sites.utils import get_initial_page_elements


class JSONMigrationUtilsTestCase(TestCase):
    def test_initial_page_elements(self):
        initial = get_initial_page_elements()

        self.assertEqual(initial['embargo'], {"content": []})

        element = initial['index']['content'][0]['children']['column-1'][0]

        self.assertEqual(element['options']['text-content'], {
            'en': 'We just took care of the Open edX tech stuff so you can focus on education!',
        })
