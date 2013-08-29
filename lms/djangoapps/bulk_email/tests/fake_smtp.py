"""
Fake SMTP Server used for testing error handling for sending email.
We could have mocked smptlib to raise connection errors, but this simulates
connection errors from an SMTP server.
"""
import smtpd
import socket
import asyncore
import asynchat
import errno


class FakeSMTPChannel(smtpd.SMTPChannel):
    """
    A fake SMTPChannel for sending fake error response through socket.
    This causes smptlib to raise an SMTPConnectError.

    Adapted from http://hg.python.org/cpython/file/2.7/Lib/smtpd.py
    """
    # Disable pylint warnings that arise from subclassing SMTPChannel
    # and calling init -- overriding SMTPChannel's init to return error
    # message but keeping the rest of the class.
    # pylint: disable=W0231, W0233
    def __init__(self, server, conn, addr):
        asynchat.async_chat.__init__(self, conn)
        self.__server = server
        self.__conn = conn
        self.__addr = addr
        self.__line = []
        self.__state = self.COMMAND
        self.__greeting = 0
        self.__mailfrom = None
        self.__rcpttos = []
        self.__data = ''
        self.__fqdn = socket.getfqdn()
        try:
            self.__peer = conn.getpeername()
        except socket.error, err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            self.close()
            if err[0] != errno.ENOTCONN:
                raise
            return
        self.push('421 SMTP Server error: too many concurrent sessions, please try again later.')
        self.set_terminator('\r\n')


class FakeSMTPServer(smtpd.SMTPServer):
    """A fake SMTP server for generating different smptlib exceptions."""
    def __init__(self, *args, **kwargs):
        smtpd.SMTPServer.__init__(self, *args, **kwargs)
        self.errtype = None
        self.response = None

    def set_errtype(self, errtype, response=''):
        """Specify the type of error to cause smptlib to raise, with optional response string.

        `errtype` -- "DATA": The server will cause smptlib to throw SMTPDataError.
                     "CONN": The server will cause smptlib to throw SMTPConnectError.
                     "DISCONN": The server will cause smptlib to throw SMTPServerDisconnected.

        """
        self.errtype = errtype
        self.response = response

    def handle_accept(self):
        if self.errtype == "DISCONN":
            self.accept()
        elif self.errtype == "CONN":
            pair = self.accept()
            if pair is not None:
                conn, addr = pair
                _channel = FakeSMTPChannel(self, conn, addr)
        else:
            smtpd.SMTPServer.handle_accept(self)

    def process_message(self, *_args, **_kwargs):
        if self.errtype == "DATA":
            # After failing on the first email, succeed on the rest.
            self.errtype = None
            return self.response
        else:
            return None

    def serve_forever(self):
        """Start the server running until close() is called on the server."""
        asyncore.loop()
