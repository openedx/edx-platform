#!/usr/bin/python

from __future__ import unicode_literals

from .. import core

CONTENT_TYPE_LATEST = str('application/openmetrics-text; version=0.0.1; charset=utf-8')
'''Content type of the latest OpenMetrics text format'''


def generate_latest(registry):
    '''Returns the metrics from the registry in latest text format as a string.'''
    output = []
    for metric in registry.collect():
        mname = metric.name
        output.append('# HELP {0} {1}\n'.format(
            mname, metric.documentation.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"')))
        output.append('# TYPE {0} {1}\n'.format(mname, metric.type))
        if metric.unit:
            output.append('# UNIT {0} {1}\n'.format(mname, metric.unit))
        for s in metric.samples:
            if s.labels:
                labelstr = '{{{0}}}'.format(','.join(
                    ['{0}="{1}"'.format(
                     k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                     for k, v in sorted(s.labels.items())]))
            else:
                labelstr = ''
            if s.exemplar:
                if metric.type not in ('histogram', 'gaugehistogram') or not s.name.endswith('_bucket'):
                    raise ValueError("Metric {0} has exemplars, but is not a histogram bucket".format(metric.name))
                labels = '{{{0}}}'.format(','.join(
                    ['{0}="{1}"'.format(
                     k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                     for k, v in sorted(s.exemplar.labels.items())]))
                if s.exemplar.timestamp is not None:
                    exemplarstr = ' # {0} {1} {2}'.format(
                        labels,
                        core._floatToGoString(s.exemplar.value),
                        s.exemplar.timestamp,
                    )
                else:
                    exemplarstr = ' # {0} {1}'.format(
                        labels,
                        core._floatToGoString(s.exemplar.value),
                    )
            else:
                exemplarstr = ''
            timestamp = ''
            if s.timestamp is not None:
                timestamp = ' {0}'.format(s.timestamp)
            output.append('{0}{1} {2}{3}{4}\n'.format(
                s.name,
                labelstr,
                core._floatToGoString(s.value),
                timestamp,
                exemplarstr,
            ))
    output.append('# EOF\n')
    return ''.join(output).encode('utf-8')
