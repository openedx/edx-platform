import threading
from bulk_email.tests.fake_smtp import FakeSMTPServer


class FakeSMTPServerThread(threading.Thread):
    """
    Thread for running a fake SMTP server for testing email
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.is_ready = threading.Event()
        self.error = None
        self.server = None
        super(FakeSMTPServerThread, self).__init__()

    def start(self):
        self.daemon = True
        super(FakeSMTPServerThread, self).start()
        self.is_ready.wait()
        if self.error:
            raise self.error

    def stop(self):
        if hasattr(self, 'server'):
            self.server.close()
        self.join()

    def run(self):
        """
        Sets up the test smtp server and handle requests
        """
        try:
            self.server = FakeSMTPServer((self.host, self.port), None)
            self.is_ready.set()
            self.server.serve_forever()
        except Exception, e:
            self.error = e
            self.is_ready.set()
