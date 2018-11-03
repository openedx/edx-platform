#!/usr/bin/python

from __future__ import unicode_literals

import math

from .. import core

try:
    import StringIO
except ImportError:
    # Python 3
    import io as StringIO



def text_string_to_metric_families(text):
    """Parse Openmetrics text format from a unicode string.

    See text_fd_to_metric_families.
    """
    for metric_family in text_fd_to_metric_families(StringIO.StringIO(text)):
        yield metric_family


def _unescape_help(text):
    result = []
    slash = False

    for char in text:
        if slash:
            if char == '\\':
                result.append('\\')
            elif char == '"':
                result.append('"')
            elif char == 'n':
                result.append('\n')
            else:
                result.append('\\' + char)
            slash = False
        else:
            if char == '\\':
                slash = True
            else:
                result.append(char)

    if slash:
        result.append('\\')

    return ''.join(result)


def _parse_value(value):
    value = ''.join(value)
    if value != value.strip():
        raise ValueError("Invalid value: {0!r}".format(value))
    try:
        return int(value)
    except ValueError:
        return float(value)


def _parse_timestamp(timestamp):
    timestamp = ''.join(timestamp)
    if not timestamp:
        return None
    if timestamp != timestamp.strip():
        raise ValueError("Invalid timestamp: {0!r}".format(timestamp))
    try:
        # Simple int.
        return core.Timestamp(int(timestamp), 0)
    except ValueError:
        try:
            # aaaa.bbbb. Nanosecond resolution supported.
            parts = timestamp.split('.', 1)
            return core.Timestamp(int(parts[0]), int(parts[1][:9].ljust(9, "0")))
        except ValueError:
            # Float.
            ts = float(timestamp)
            if math.isnan(ts) or math.isinf(ts):
                raise ValueError("Invalid timestamp: {0!r}".format(timestamp))
            return ts


def _parse_labels(it, text):
    # The { has already been parsed.
    state = 'startoflabelname'
    labelname = []
    labelvalue = []
    labels = {}

    for char in it:
        if state == 'startoflabelname':
            if char == '}':
                state = 'endoflabels'
            else:
                state = 'labelname'
                labelname.append(char)
        elif state == 'labelname':
            if char == '=':
                state = 'labelvaluequote'
            else:
                labelname.append(char)
        elif state == 'labelvaluequote':
            if char == '"':
                state = 'labelvalue'
            else:
                raise ValueError("Invalid line: " + text)
        elif state == 'labelvalue':
            if char == '\\':
                state = 'labelvalueslash'
            elif char == '"':
                if not core._METRIC_LABEL_NAME_RE.match(''.join(labelname)):
                    raise ValueError("Invalid line: " + text)
                labels[''.join(labelname)] = ''.join(labelvalue)
                labelname = []
                labelvalue = []
                state = 'endoflabelvalue'
            else:
                labelvalue.append(char)
        elif state == 'endoflabelvalue':
            if char == ',':
                state = 'labelname'
            elif char == '}':
                state = 'endoflabels'
            else:
                raise ValueError("Invalid line: " + text)
        elif state == 'labelvalueslash':
            state = 'labelvalue'
            if char == '\\':
                labelvalue.append('\\')
            elif char == 'n':
                labelvalue.append('\n')
            elif char == '"':
                labelvalue.append('"')
            else:
                labelvalue.append('\\' + char)
        elif state == 'endoflabels':
            if char == ' ':
                break
            else:
                raise ValueError("Invalid line: " + text)
    return labels


def _parse_sample(text):
    name = []
    value = []
    timestamp = []
    labels = {}
    exemplar_value = []
    exemplar_timestamp = []
    exemplar_labels = None

    state = 'name'

    it = iter(text)
    for char in it:
        if state == 'name':
            if char == '{':
                labels = _parse_labels(it, text)
                # Space has already been parsed.
                state = 'value'
            elif char == ' ':
                state = 'value'
            else:
                name.append(char)
        elif state == 'value':
            if char == ' ':
                state = 'timestamp'
            else:
                value.append(char)
        elif state == 'timestamp':
            if char == '#' and not timestamp:
                state = 'exemplarspace'
            elif char == ' ':
                state = 'exemplarhash'
            else:
                timestamp.append(char)
        elif state == 'exemplarhash':
            if char == '#':
                state = 'exemplarspace'
            else:
                raise ValueError("Invalid line: " + text)
        elif state == 'exemplarspace':
            if char == ' ':
                state = 'exemplarstartoflabels'
            else:
                raise ValueError("Invalid line: " + text)
        elif state == 'exemplarstartoflabels':
            if char == '{':
                exemplar_labels = _parse_labels(it, text)
                # Space has already been parsed.
                state = 'exemplarvalue'
            else:
                raise ValueError("Invalid line: " + text)
        elif state == 'exemplarvalue':
            if char == ' ':
                state = 'exemplartimestamp'
            else:
                exemplar_value.append(char)
        elif state == 'exemplartimestamp':
            exemplar_timestamp.append(char)

    # Trailing space after value.
    if state == 'timestamp' and not timestamp:
        raise ValueError("Invalid line: " + text)

    # Trailing space after value.
    if state == 'exemplartimestamp' and not exemplar_timestamp:
        raise ValueError("Invalid line: " + text)

    # Incomplete exemplar.
    if state in ['exemplarhash', 'exemplarspace', 'exemplarstartoflabels']:
        raise ValueError("Invalid line: " + text)

    if not value:
        raise ValueError("Invalid line: " + text)
    value = ''.join(value)
    val = _parse_value(value)
    ts = _parse_timestamp(timestamp)
    exemplar = None
    if exemplar_labels is not None:
        exemplar_length = sum([len(k) + len(v) + 3 for k, v in exemplar_labels.items()]) + 2
        if exemplar_length > 64:
            raise ValueError("Exmplar labels are too long: " + text)
        exemplar = core.Exemplar(
            exemplar_labels,
            _parse_value(exemplar_value),
            _parse_timestamp(exemplar_timestamp),
        )

    return core.Sample(''.join(name), labels, val, ts, exemplar)


def _group_for_sample(sample, name, typ):
    if typ == 'info':
        # We can't distinguish between groups for info metrics.
        return {}
    if typ == 'summary' and sample.name == name:
        d = sample.labels.copy()
        del d['quantile']
        return d
    if typ == 'stateset':
        d = sample.labels.copy()
        del d[name]
        return d
    if typ in ['histogram', 'gaugehistogram'] and sample.name == name + '_bucket':
        d = sample.labels.copy()
        del d['le']
        return d
    return sample.labels


def _check_histogram(samples, name):
    group = None
    timestamp = None

    def do_checks():
        if bucket != float('+Inf'):
            raise ValueError("+Inf bucket missing: " + name)
        if count is not None and value != count:
            raise ValueError("Count does not match +Inf value: " + name)

    for s in samples:
        suffix = s.name[len(name):]
        g = _group_for_sample(s, name, 'histogram')
        if g != group or s.timestamp != timestamp:
            if group is not None:
                do_checks()
            count = None
            bucket = -1
            value = 0
        group = g
        timestamp = s.timestamp

        if suffix == '_bucket':
            b = float(s.labels['le'])
            if b <= bucket:
                raise ValueError("Buckets out of order: " + name)
            if s.value < value:
                raise ValueError("Bucket values out of order: " + name)
            bucket = b
            value = s.value
        elif suffix in ['_count', '_gcount']:
            count = s.value
    if group is not None:
        do_checks()


def text_fd_to_metric_families(fd):
    """Parse Prometheus text format from a file descriptor.

    This is a laxer parser than the main Go parser,
    so successful parsing does not imply that the parsed
    text meets the specification.

    Yields core.Metric's.
    """
    name = None
    allowed_names = []
    eof = False

    seen_metrics = set()

    def build_metric(name, documentation, typ, unit, samples):
        if name in seen_metrics:
            raise ValueError("Duplicate metric: " + name)
        seen_metrics.add(name)
        if typ is None:
            typ = 'unknown'
        if documentation is None:
            documentation = ''
        if unit is None:
            unit = ''
        if unit and not name.endswith("_" + unit):
            raise ValueError("Unit does not match metric name: " + name)
        if unit and typ in ['info', 'stateset']:
            raise ValueError("Units not allowed for this metric type: " + name)
        if typ in ['histogram', 'gaugehistogram']:
            _check_histogram(samples, name)
        metric = core.Metric(name, documentation, typ, unit)
        # TODO: check labelvalues are valid utf8
        metric.samples = samples
        return metric

    for line in fd:
        if line[-1] == '\n':
            line = line[:-1]

        if eof:
            raise ValueError("Received line after # EOF: " + line)

        if line == '# EOF':
            eof = True
        elif line.startswith('#'):
            parts = line.split(' ', 3)
            if len(parts) < 4:
                raise ValueError("Invalid line: " + line)
            if parts[2] == name and samples:
                raise ValueError("Received metadata after samples: " + line)
            if parts[2] != name:
                if name is not None:
                    yield build_metric(name, documentation, typ, unit, samples)
                # New metric
                name = parts[2]
                unit = None
                typ = None
                documentation = None
                group = None
                seen_groups = set()
                group_timestamp = None
                group_timestamp_samples = set()
                samples = []
                allowed_names = [parts[2]]

            if parts[1] == 'HELP':
                if documentation is not None:
                    raise ValueError("More than one HELP for metric: " + line)
                if len(parts) == 4:
                    documentation = _unescape_help(parts[3])
                elif len(parts) == 3:
                    raise ValueError("Invalid line: " + line)
            elif parts[1] == 'TYPE':
                if typ is not None:
                    raise ValueError("More than one TYPE for metric: " + line)
                typ = parts[3]
                if typ == 'untyped':
                    raise ValueError("Invalid TYPE for metric: " + line)
                allowed_names = {
                    'counter': ['_total', '_created'],
                    'summary': ['_count', '_sum', '', '_created'],
                    'histogram': ['_count', '_sum', '_bucket', 'created'],
                    'gaugehistogram': ['_gcount', '_gsum', '_bucket'],
                    'info': ['_info'],
                }.get(typ, [''])
                allowed_names = [name + n for n in allowed_names]
            elif parts[1] == 'UNIT':
                if unit is not None:
                    raise ValueError("More than one UNIT for metric: " + line)
                unit = parts[3]
            else:
                raise ValueError("Invalid line: " + line)
        else:
            sample = _parse_sample(line)
            if sample.name not in allowed_names:
                if name is not None:
                    yield build_metric(name, documentation, typ, unit, samples)
                # Start an unknown metric.
                name = sample.name
                documentation = None
                unit = None
                typ = 'unknown'
                samples = []
                group = None
                group_timestamp = None
                group_timestamp_samples = set()
                seen_groups = set()
                allowed_names = [sample.name]

            if typ == 'stateset' and name not in sample.labels:
                raise ValueError("Stateset missing label: " + line)
            if (typ in ['histogram', 'gaugehistogram'] and name + '_bucket' == sample.name
                    and float(sample.labels.get('le', -1)) < 0):
                raise ValueError("Invalid le label: " + line)
            if (typ == 'summary' and name == sample.name
                    and not (0 <= float(sample.labels.get('quantile', -1)) <= 1)):
                raise ValueError("Invalid quantile label: " + line)

            g = tuple(sorted(_group_for_sample(sample, name, typ).items()))
            if group is not None and g != group and g in seen_groups:
                raise ValueError("Invalid metric grouping: " + line)
            if group is not None and g == group:
                if (sample.timestamp is None) != (group_timestamp is None):
                    raise ValueError("Mix of timestamp presence within a group: " + line)
                if group_timestamp is not None and group_timestamp > sample.timestamp and typ != 'info':
                    raise ValueError("Timestamps went backwards within a group: " + line)
            else:
                group_timestamp_samples = set()

            series_id = (sample.name, tuple(sorted(sample.labels.items())))
            if sample.timestamp != group_timestamp or series_id not in group_timestamp_samples:
                # Not a duplicate due to timestamp truncation.
                samples.append(sample)
            group_timestamp_samples.add(series_id)

            group = g
            group_timestamp = sample.timestamp
            seen_groups.add(g)

            if typ == 'stateset' and sample.value not in [0, 1]:
                raise ValueError("Stateset samples can only have values zero and one: " + line)
            if typ == 'info' and sample.value != 1:
                raise ValueError("Info samples can only have value one: " + line)
            if sample.name[len(name):] in ['_total', '_sum', '_count', '_bucket'] and math.isnan(sample.value):
                raise ValueError("Counter-like samples cannot be NaN: " + line)
            if sample.exemplar and not (
                    typ in ['histogram', 'gaugehistogram']
                    and sample.name.endswith('_bucket')):
                raise ValueError("Invalid line only histogram/gaugehistogram buckets can have exemplars: " + line)

    if name is not None:
        yield build_metric(name, documentation, typ, unit, samples)

    if not eof:
        raise ValueError("Missing # EOF at end")
