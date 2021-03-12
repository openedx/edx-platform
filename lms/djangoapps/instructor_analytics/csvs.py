"""
Student and course analytics.

Format and create csv responses
"""


import csv

import six
from six.moves import map
from django.http import HttpResponse


def create_csv_response(filename, header, datarows):
    """
    Create an HttpResponse with an attached .csv file

    header   e.g. ['Name', 'Email']
    datarows e.g. [['Jim', 'jim@edy.org'], ['Jake', 'jake@edy.org'], ...]

    The data in `header` and `datarows` must be either Unicode strings,
    or ASCII-only bytestrings.

    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = u'attachment; filename={0}'.format(filename)
    csvwriter = csv.writer(
        response,
        dialect='excel',
        quotechar='"',
        quoting=csv.QUOTE_ALL)

    encoded_header = [six.text_type(s) for s in header]
    csvwriter.writerow(encoded_header)

    for datarow in datarows:
        encoded_row = [six.text_type(s) for s in datarow]
        csvwriter.writerow(encoded_row)

    return response


def format_dictlist(dictlist, features):
    """
    Convert a list of dictionaries to be compatible with create_csv_response

    `dictlist` is a list of dictionaries
        all dictionaries should have keys from features
    `features` is a list of features

    example code:
    dictlist = [
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
        }
    ]

    header, datarows = format_dictlist(dictlist, ['label1', 'label4'])

    # results in
    header = ['label1', 'label4']
    datarows = [['value-1,1', 'value-1,4'],
                ['value-2,1', 'value-2,4']]
    }
    """

    def dict_to_entry(dct):
        """ Convert dictionary to a list for a csv row """
        relevant_items = [(k, v) for (k, v) in dct.items() if k in features]
        ordered = sorted(relevant_items, key=lambda k_v: header.index(k_v[0]))
        vals = [v for (_, v) in ordered]
        return vals

    header = features
    datarows = list(map(dict_to_entry, dictlist))

    return header, datarows


def format_instances(instances, features):
    """
    Convert a list of instances into a header list and datarows list.

    `header` is just `features` e.g. ['username', 'email']
    `datarows` is a list of lists, each sublist representing a row in a table
        e.g. [['username1', 'email1@email.com'], ['username2', 'email2@email.com']]
        for `instances` of length 2.

    `instances` is a list of instances, e.g. list of User's
    `features` is a list of features
        a feature is a string for which getattr(obj, feature) is valid

    Returns header and datarows, formatted for input in create_csv_response
    """
    header = features
    datarows = [[getattr(x, f) for f in features] for x in instances]
    return header, datarows
