""" Tests for analytics.csvs """

from django.test import TestCase

from analytics.csvs import create_csv_response, format_dictlist


class TestAnalyticsCSVS(TestCase):
    '''Test analytics rendering of csv files.'''

    def test_create_csv_response_nodata(self):
        header = ['Name', 'Email']
        datarows = []

        res = create_csv_response('robot.csv', header, datarows)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertEqual(res['Content-Disposition'], 'attachment; filename={0}'.format('robot.csv'))
        self.assertEqual(res.content.strip(), '"Name","Email"')

    def test_create_csv_response(self):
        header = ['Name', 'Email']
        datarows = [['Jim', 'jim@edy.org'], ['Jake', 'jake@edy.org'], ['Jeeves', 'jeeves@edy.org']]

        res = create_csv_response('robot.csv', header, datarows)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertEqual(res['Content-Disposition'], 'attachment; filename={0}'.format('robot.csv'))
        self.assertEqual(res.content.strip(), '"Name","Email"\r\n"Jim","jim@edy.org"\r\n"Jake","jake@edy.org"\r\n"Jeeves","jeeves@edy.org"')

    def test_create_csv_response_empty(self):
        header = []
        datarows = []

        res = create_csv_response('robot.csv', header, datarows)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertEqual(res['Content-Disposition'], 'attachment; filename={0}'.format('robot.csv'))
        self.assertEqual(res.content.strip(), '')

    def test_format_dictlist(self):
        data_in = [
            {
                'label1': 'value-1,1',
                'label2': 'value-1,2',
                'label3': 'value-1,3',
                'label4': 'value-1,4',
            },
            {
                'label1': 'value-2,1',
                'label2': 'value-2,2',
                'label3': 'value-2,3',
                'label4': 'value-2,4',
            },
        ]

        data_out = {
            'header': ['label1', 'label2', 'label3', 'label4'],
            'datarows': [['value-1,1', 'value-1,2', 'value-1,3', 'value-1,4'],
                         ['value-2,1', 'value-2,2', 'value-2,3', 'value-2,4']],
        }

        self.assertEqual(format_dictlist(data_in), data_out)

    def test_format_dictlist_empty(self):
        self.assertEqual(format_dictlist([]), {
            'header': [],
            'datarows': [],
        })
