""" Tests for analytics.csvs """

from django.test import TestCase
from nose.tools import raises

from analytics.csvs import create_csv_response, format_dictlist, format_instances


class TestAnalyticsCSVS(TestCase):
    """ Test analytics rendering of csv files."""

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


class TestAnalyticsFormatDictlist(TestCase):
    """ Test format_dictlist method """

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

    def test_create_csv_response(self):
        header = ['Name', 'Email']
        datarows = [['Jim', 'jim@edy.org'], ['Jake', 'jake@edy.org'], ['Jeeves', 'jeeves@edy.org']]

        res = create_csv_response('robot.csv', header, datarows)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertEqual(res['Content-Disposition'], 'attachment; filename={0}'.format('robot.csv'))
        self.assertEqual(res.content.strip(), '"Name","Email"\r\n"Jim","jim@edy.org"\r\n"Jake","jake@edy.org"\r\n"Jeeves","jeeves@edy.org"')


class TestAnalyticsFormatInstances(TestCase):
    """ test format_instances method """
    class TestDataClass(object):
        """ Test class to generate objects for format_instances """
        def __init__(self):
            self.a_var = 'aval'
            self.b_var = 'bval'
            self.c_var = 'cval'

        @property
        def d_var(self):
            """ accessor to see if they work too """
            return 'dval'

    def setUp(self):
        self.instances = [self.TestDataClass() for _ in xrange(5)]

    def test_format_instances_response(self):
        features = ['a_var', 'c_var', 'd_var']
        header, datarows = format_instances(self.instances, features)
        self.assertEqual(header, ['a_var', 'c_var', 'd_var'])
        self.assertEqual(datarows, [[
            'aval',
            'cval',
            'dval',
        ] for _ in xrange(len(self.instances))])

    def test_format_instances_response_noinstances(self):
        features = ['a_var']
        header, datarows = format_instances([], features)
        self.assertEqual(header, features)
        self.assertEqual(datarows, [])

    def test_format_instances_response_nofeatures(self):
        header, datarows = format_instances(self.instances, [])
        self.assertEqual(header, [])
        self.assertEqual(datarows, [[] for _ in xrange(len(self.instances))])

    @raises(AttributeError)
    def test_format_instances_response_nonexistantfeature(self):
        format_instances(self.instances, ['robot_not_a_real_feature'])
