#!/usr/bin/python

from __future__ import unicode_literals

import base64
from contextlib import closing
import os
import socket
import sys
import threading
from wsgiref.simple_server import make_server, WSGIRequestHandler

from prometheus_client import core
from prometheus_client.openmetrics import exposition as openmetrics

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urllib2 import build_opener, Request, HTTPHandler
    from urllib import quote_plus
    from urlparse import parse_qs, urlparse
except ImportError:
    # Python 3
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.request import build_opener, Request, HTTPHandler
    from urllib.parse import quote_plus, parse_qs, urlparse


CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
'''Content type of the latest text format'''

PYTHON26_OR_OLDER = sys.version_info < (2, 7)


def make_wsgi_app(registry=core.REGISTRY):
    '''Create a WSGI app which serves the metrics from a registry.'''
    def prometheus_app(environ, start_response):
        params = parse_qs(environ.get('QUERY_STRING', ''))
        r = registry
        encoder, content_type = choose_encoder(environ.get('HTTP_ACCEPT'))
        if 'name[]' in params:
            r = r.restricted_registry(params['name[]'])
        output = encoder(r)

        status = str('200 OK')
        headers = [(str('Content-type'), content_type)]
        start_response(status, headers)
        return [output]
    return prometheus_app


class _SilentHandler(WSGIRequestHandler):
    """WSGI handler that does not log requests."""

    def log_message(self, format, *args):
        """Log nothing."""


def start_wsgi_server(port, addr='', registry=core.REGISTRY):
    """Starts a WSGI server for prometheus metrics as a daemon thread."""
    app = make_wsgi_app(registry)
    httpd = make_server(addr, port, app, handler_class=_SilentHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()


def generate_latest(registry=core.REGISTRY):
    '''Returns the metrics from the registry in latest text format as a string.'''

    def sample_line(s):
        if s.labels:
            labelstr = '{{{0}}}'.format(','.join(
                ['{0}="{1}"'.format(
                 k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                 for k, v in sorted(s.labels.items())]))
        else:
            labelstr = ''
        timestamp = ''
        if s.timestamp is not None:
            # Convert to milliseconds.
            timestamp = ' {0:d}'.format(int(float(s.timestamp) * 1000))
        return '{0}{1} {2}{3}\n'.format(
            s.name, labelstr, core._floatToGoString(s.value), timestamp)

    output = []
    for metric in registry.collect():
        mname = metric.name
        mtype = metric.type
        # Munging from OpenMetrics into Prometheus format.
        if mtype == 'counter':
            mname = mname + '_total'
        elif mtype == 'info':
            mname = mname + '_info'
            mtype = 'gauge'
        elif mtype == 'stateset':
            mtype = 'gauge'
        elif mtype == 'gaugehistogram':
            # A gauge histogram is really a gauge,
            # but this captures the strucutre better.
            mtype = 'histogram'
        elif mtype == 'unknown':
            mtype = 'untyped'

        output.append('# HELP {0} {1}\n'.format(
            mname, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
        output.append('# TYPE {0} {1}\n'.format(mname, mtype))

        om_samples = {}
        for s in metric.samples:
            for suffix in ['_created', '_gsum', '_gcount']:
                if s.name == metric.name + suffix:
                    # OpenMetrics specific sample, put in a gauge at the end.
                    om_samples.setdefault(suffix, []).append(sample_line(s))
                    break
            else:
                output.append(sample_line(s))
        for suffix, lines in sorted(om_samples.items()):
            output.append('# TYPE {0}{1} gauge\n'.format(metric.name, suffix))
            output.extend(lines)
    return ''.join(output).encode('utf-8')


def choose_encoder(accept_header):
    accept_header = accept_header or ''
    for accepted in accept_header.split(','):
        if accepted.split(';')[0].strip() == 'application/openmetrics-text':
            return (openmetrics.generate_latest,
                    openmetrics.CONTENT_TYPE_LATEST)
    return (generate_latest, CONTENT_TYPE_LATEST)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler that gives metrics from ``core.REGISTRY``."""
    registry = core.REGISTRY

    def do_GET(self):
        registry = self.registry
        params = parse_qs(urlparse(self.path).query)
        encoder, content_type = choose_encoder(self.headers.get('Accept'))
        if 'name[]' in params:
            registry = registry.restricted_registry(params['name[]'])
        try:
            output = encoder(registry)
        except:
            self.send_error(500, 'error generating metric output')
            raise
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, format, *args):
        """Log nothing."""

    @staticmethod
    def factory(registry):
        """Returns a dynamic MetricsHandler class tied
           to the passed registry.
        """
        # This implementation relies on MetricsHandler.registry
        #  (defined above and defaulted to core.REGISTRY).

        # As we have unicode_literals, we need to create a str()
        #  object for type().
        cls_name = str('MetricsHandler')
        MyMetricsHandler = type(cls_name, (MetricsHandler, object),
                                {"registry": registry})
        return MyMetricsHandler


class _ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    """Thread per request HTTP server."""


def start_http_server(port, addr='', registry=core.REGISTRY):
    """Starts an HTTP server for prometheus metrics as a daemon thread"""
    CustomMetricsHandler = MetricsHandler.factory(registry)
    httpd = _ThreadingSimpleServer((addr, port), CustomMetricsHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()


def write_to_textfile(path, registry):
    '''Write metrics to the given path.

    This is intended for use with the Node exporter textfile collector.
    The path must end in .prom for the textfile collector to process it.'''
    tmppath = '%s.%s.%s' % (path, os.getpid(), threading.current_thread().ident)
    with open(tmppath, 'wb') as f:
        f.write(generate_latest(registry))
    # rename(2) is atomic.
    os.rename(tmppath, path)


def default_handler(url, method, timeout, headers, data):
    '''Default handler that implements HTTP/HTTPS connections.

    Used by the push_to_gateway functions. Can be re-used by other handlers.'''
    def handle():
        request = Request(url, data=data)
        request.get_method = lambda: method
        for k, v in headers:
            request.add_header(k, v)
        resp = build_opener(HTTPHandler).open(request, timeout=timeout)
        if resp.code >= 400:
            raise IOError("error talking to pushgateway: {0} {1}".format(
                resp.code, resp.msg))

    return handle


def basic_auth_handler(url, method, timeout, headers, data, username=None, password=None):
    '''Handler that implements HTTP/HTTPS connections with Basic Auth.

    Sets auth headers using supplied 'username' and 'password', if set.
    Used by the push_to_gateway functions. Can be re-used by other handlers.'''
    def handle():
        '''Handler that implements HTTP Basic Auth.
        '''
        if username is not None and password is not None:
            auth_value = '{0}:{1}'.format(username, password).encode('utf-8')
            auth_token = base64.b64encode(auth_value)
            auth_header = b'Basic ' + auth_token
            headers.append(['Authorization', auth_header])
        default_handler(url, method, timeout, headers, data)()

    return handle


def push_to_gateway(
        gateway, job, registry, grouping_key=None, timeout=30,
        handler=default_handler):
    '''Push metrics to the given pushgateway.

    `gateway` the url for your push gateway. Either of the form
              'http://pushgateway.local', or 'pushgateway.local'.
              Scheme defaults to 'http' if none is provided
    `job` is the job label to be attached to all pushed metrics
    `registry` is an instance of CollectorRegistry
    `grouping_key` please see the pushgateway documentation for details.
                   Defaults to None
    `timeout` is how long push will attempt to connect before giving up.
              Defaults to 30s, can be set to None for no timeout.
    `handler` is an optional function which can be provided to perform
              requests to the 'gateway'.
              Defaults to None, in which case an http or https request
              will be carried out by a default handler.
              If not None, the argument must be a function which accepts
              the following arguments:
              url, method, timeout, headers, and content
              May be used to implement additional functionality not
              supported by the built-in default handler (such as SSL
              client certicates, and HTTP authentication mechanisms).
              'url' is the URL for the request, the 'gateway' argument
              described earlier will form the basis of this URL.
              'method' is the HTTP method which should be used when
              carrying out the request.
              'timeout' requests not successfully completed after this
              many seconds should be aborted.  If timeout is None, then
              the handler should not set a timeout.
              'headers' is a list of ("header-name","header-value") tuples
              which must be passed to the pushgateway in the form of HTTP
              request headers.
              The function should raise an exception (e.g. IOError) on
              failure.
              'content' is the data which should be used to form the HTTP
              Message Body.

    This overwrites all metrics with the same job and grouping_key.
    This uses the PUT HTTP method.'''
    _use_gateway('PUT', gateway, job, registry, grouping_key, timeout, handler)


def pushadd_to_gateway(
        gateway, job, registry, grouping_key=None, timeout=30,
        handler=default_handler):
    '''PushAdd metrics to the given pushgateway.

    `gateway` the url for your push gateway. Either of the form
              'http://pushgateway.local', or 'pushgateway.local'.
              Scheme defaults to 'http' if none is provided
    `job` is the job label to be attached to all pushed metrics
    `registry` is an instance of CollectorRegistry
    `grouping_key` please see the pushgateway documentation for details.
                   Defaults to None
    `timeout` is how long push will attempt to connect before giving up.
              Defaults to 30s, can be set to None for no timeout.
    `handler` is an optional function which can be provided to perform
              requests to the 'gateway'.
              Defaults to None, in which case an http or https request
              will be carried out by a default handler.
              See the 'prometheus_client.push_to_gateway' documentation
              for implementation requirements.

    This replaces metrics with the same name, job and grouping_key.
    This uses the POST HTTP method.'''
    _use_gateway('POST', gateway, job, registry, grouping_key, timeout, handler)


def delete_from_gateway(
        gateway, job, grouping_key=None, timeout=30, handler=default_handler):
    '''Delete metrics from the given pushgateway.

    `gateway` the url for your push gateway. Either of the form
              'http://pushgateway.local', or 'pushgateway.local'.
              Scheme defaults to 'http' if none is provided
    `job` is the job label to be attached to all pushed metrics
    `grouping_key` please see the pushgateway documentation for details.
                   Defaults to None
    `timeout` is how long delete will attempt to connect before giving up.
              Defaults to 30s, can be set to None for no timeout.
    `handler` is an optional function which can be provided to perform
              requests to the 'gateway'.
              Defaults to None, in which case an http or https request
              will be carried out by a default handler.
              See the 'prometheus_client.push_to_gateway' documentation
              for implementation requirements.

    This deletes metrics with the given job and grouping_key.
    This uses the DELETE HTTP method.'''
    _use_gateway('DELETE', gateway, job, None, grouping_key, timeout, handler)


def _use_gateway(method, gateway, job, registry, grouping_key, timeout, handler):
    gateway_url = urlparse(gateway)
    if not gateway_url.scheme or (PYTHON26_OR_OLDER and gateway_url.scheme not in ['http', 'https']):
        gateway = 'http://{0}'.format(gateway)
    url = '{0}/metrics/job/{1}'.format(gateway, quote_plus(job))

    data = b''
    if method != 'DELETE':
        data = generate_latest(registry)

    if grouping_key is None:
        grouping_key = {}
    url += ''.join(
        '/{0}/{1}'.format(quote_plus(str(k)), quote_plus(str(v)))
        for k, v in sorted(grouping_key.items()))

    handler(
        url=url, method=method, timeout=timeout,
        headers=[('Content-Type', CONTENT_TYPE_LATEST)], data=data,
    )()


def instance_ip_grouping_key():
    '''Grouping key with instance set to the IP Address of this host.'''
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.connect(('localhost', 0))
        return {'instance': s.getsockname()[0]}
