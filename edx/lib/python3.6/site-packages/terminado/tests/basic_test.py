# basic_tests.py -- Basic unit tests for Terminado

# Copyright (c) Jupyter Development Team
# Copyright (c) 2014, Ramalingam Saravanan <sarava@sarava.net>
# Distributed under the terms of the Simplified BSD License.

from __future__ import absolute_import, print_function

import unittest
from terminado import *
import tornado
import tornado.httpserver
from tornado.httpclient import HTTPError
from tornado.ioloop import IOLoop
import tornado.testing
import datetime
import logging
import json
import os
import re


#
# The timeout we use to assume no more messages are coming
# from the sever.
#
DONE_TIMEOUT = 1.0
os.environ['ASYNC_TEST_TIMEOUT'] = "20"     # Global test case timeout

MAX_TERMS = 3                               # Testing thresholds

class TestTermClient(object):
    """Test connection to a terminal manager"""
    def __init__(self, websocket):
        self.ws = websocket
        self.pending_read = None

    @tornado.gen.coroutine
    def read_msg(self):

        # Because the Tornado Websocket client has no way to cancel
        # a pending read, we have to keep track of them...
        if self.pending_read is None:
            self.pending_read = self.ws.read_message()

        response = yield self.pending_read
        self.pending_read = None
        if response:
            response = json.loads(response)
        raise tornado.gen.Return(response)

    @tornado.gen.coroutine
    def read_all_msg(self, timeout=DONE_TIMEOUT):
        """Read messages until read times out"""
        msglist = []
        delta = datetime.timedelta(seconds=timeout)
        while True:
            try:
                mf = self.read_msg()
                msg = yield tornado.gen.with_timeout(delta, mf)
            except tornado.gen.TimeoutError:
                raise tornado.gen.Return(msglist)

            msglist.append(msg)

    def write_msg(self, msg):
        self.ws.write_message(json.dumps(msg))

    @tornado.gen.coroutine
    def read_stdout(self, timeout=DONE_TIMEOUT):
        """Read standard output until timeout read reached,
           return stdout and any non-stdout msgs received."""
        msglist = yield self.read_all_msg(timeout)
        stdout = "".join([msg[1] for msg in msglist if msg[0] == 'stdout'])
        othermsg = [msg for msg in msglist if msg[0] != 'stdout']
        raise tornado.gen.Return((stdout, othermsg))

    def write_stdin(self, data):
        """Write to terminal stdin"""
        self.write_msg(['stdin', data])

    @tornado.gen.coroutine
    def get_pid(self):
        """Get process ID of terminal shell process"""
        yield self.read_stdout()                          # Clear out any pending
        self.write_stdin("echo $$\r")
        (stdout, extra) = yield self.read_stdout()
        if os.name == 'nt':
            match = re.search(r'echo \$\$\x1b\[0K\r\n(\d+)', stdout)
            pid = int(match.groups()[0])
        else:
            pid = int(stdout.split('\n')[1])
        raise tornado.gen.Return(pid)

    def close(self):
        self.ws.close()

class TermTestCase(tornado.testing.AsyncHTTPTestCase):

    # Factory for TestTermClient, because it has to be a Tornado co-routine.
    # See:  https://github.com/tornadoweb/tornado/issues/1161
    @tornado.gen.coroutine
    def get_term_client(self, path):
        port = self.get_http_port()
        url = 'ws://127.0.0.1:%d%s' % (port, path)
        request = tornado.httpclient.HTTPRequest(url,
                    headers={'Origin' : 'http://127.0.0.1:%d' % port})

        ws = yield tornado.websocket.websocket_connect(request)
        raise tornado.gen.Return(TestTermClient(ws))

    @tornado.gen.coroutine
    def get_term_clients(self, paths):
        tms = yield [self.get_term_client(path) for path in paths]
        raise tornado.gen.Return(tms)

    @tornado.gen.coroutine
    def get_pids(self, tm_list):
        pids = []
        for tm in tm_list:                  # Must be sequential, in case terms are shared
            pid = yield tm.get_pid()
            pids.append(pid)

        raise tornado.gen.Return(pids)

    def get_app(self):
        self.named_tm = NamedTermManager(shell_command=['bash'], 
                                            max_terminals=MAX_TERMS,
                                            ioloop=self.io_loop)
        self.single_tm = SingleTermManager(shell_command=['bash'], 
                                            ioloop=self.io_loop)
        self.unique_tm = UniqueTermManager(shell_command=['bash'], 
                                            max_terminals=MAX_TERMS,
                                            ioloop=self.io_loop)
        
        named_tm = self.named_tm
        class NewTerminalHandler(tornado.web.RequestHandler):
            """Create a new named terminal, return redirect"""
            def get(self):
                name, terminal = named_tm.new_named_terminal()
                self.redirect("/named/" + name, permanent=False)

        return tornado.web.Application([
                    (r"/new",         NewTerminalHandler),
                    (r"/named/(\w+)", TermSocket, {'term_manager': self.named_tm}),
                    (r"/single",      TermSocket, {'term_manager': self.single_tm}),
                    (r"/unique",      TermSocket, {'term_manager': self.unique_tm})
                ], debug=True)

    test_urls = ('/named/term1', '/unique', '/single')

class CommonTests(TermTestCase):
    @tornado.testing.gen_test
    def test_basic(self):
        for url in self.test_urls:
            tm = yield self.get_term_client(url)
            response = yield tm.read_msg()                    
            self.assertEqual(response, ['setup', {}])

            # Check for initial shell prompt
            response = yield tm.read_msg()
            self.assertEqual(response[0], 'stdout')
            self.assertGreater(len(response[1]), 0)
            tm.close()

    @tornado.testing.gen_test
    def test_basic_command(self):
        for url in self.test_urls:
            tm = yield self.get_term_client(url)
            yield tm.read_all_msg()
            tm.write_stdin("whoami\n")
            (stdout, other) = yield tm.read_stdout()
            if os.name == 'nt':
                assert 'whoami' in stdout
            else:
                assert stdout.startswith('who')
            assert other == []
            tm.close()

class NamedTermTests(TermTestCase):
    def test_new(self):
        response = self.fetch("/new", follow_redirects=False)
        self.assertEqual(response.code, 302)
        url = response.headers["Location"]

        # Check that the new terminal was created
        name = url.split('/')[2]
        self.assertIn(name, self.named_tm.terminals)

    @tornado.testing.gen_test
    def test_namespace(self):
        names = ["/named/1"]*2 + ["/named/2"]*2
        tms = yield self.get_term_clients(names)
        pids = yield self.get_pids(tms)

        self.assertEqual(pids[0], pids[1])
        self.assertEqual(pids[2], pids[3])
        self.assertNotEqual(pids[0], pids[3])

    @tornado.testing.gen_test
    def test_max_terminals(self):
        urls = ["/named/%d" % i for i in range(MAX_TERMS+1)]
        tms = yield self.get_term_clients(urls[:MAX_TERMS])
        pids = yield self.get_pids(tms)

        # MAX_TERMS+1 should fail
        tm = yield self.get_term_client(urls[MAX_TERMS])
        msg = yield tm.read_msg()
        self.assertEqual(msg, None)             # Connection closed

class SingleTermTests(TermTestCase):
    @tornado.testing.gen_test
    def test_single_process(self):
        tms = yield self.get_term_clients(["/single", "/single"])
        pids = yield self.get_pids(tms)
        self.assertEqual(pids[0], pids[1])

class UniqueTermTests(TermTestCase):
    @tornado.testing.gen_test
    def test_unique_processes(self):
        tms = yield self.get_term_clients(["/unique", "/unique"])
        pids = yield self.get_pids(tms)
        self.assertNotEqual(pids[0], pids[1])

    @tornado.testing.gen_test
    def test_max_terminals(self):
        tms = yield self.get_term_clients(['/unique'] * MAX_TERMS)
        pids = yield self.get_pids(tms)
        self.assertEqual(len(set(pids)), MAX_TERMS)        # All PIDs unique

        # MAX_TERMS+1 should fail
        tm = yield self.get_term_client("/unique")
        msg = yield tm.read_msg()
        self.assertEqual(msg, None)             # Connection closed

        # Close one
        tms[0].close()
        msg = yield tms[0].read_msg()           # Closed
        self.assertEquals(msg, None)

        # Should be able to open back up to MAX_TERMS
        tm = yield self.get_term_client("/unique")
        msg = yield tm.read_msg()
        self.assertEquals(msg[0], 'setup')

if __name__ == '__main__':
    unittest.main()
