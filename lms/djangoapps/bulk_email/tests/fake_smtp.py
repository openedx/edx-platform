import smtpd
import asyncore
import random
import smtplib

class FakeSMTPServer(smtpd.SMTPServer):
    """A fake SMTP server"""
    def __init__(self, *args, **kwargs):
        print "Running fake smtp server on port 1025"
        self.errtype = "SUCCESS"
        self.code = 0
        smtpd.SMTPServer.__init__(self, *args, **kwargs)
    
    def set_errtype(self, e, c):
        self.errtype = e
        self.code = c

    def process_message(self, *args, **kwargs):
        if self.errtype == "DATA":
            raise smtplib.SMTPDataError(self.code, "Data Error")
        elif self.errtype == "CONNECT":
            raise smtplib.SMTPConnectError(self.code, "Connect Error")
        elif self.errtype == "SERVERDISCONNECT":
            raise smtplib.SMTPServerDisconnected(self.code, "Server Disconnected")
        else:
            print "SUCCESS"
        pass

if __name__ == "__main__":
    smtp_server = FakeSMTPServer(('localhost', 1025), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
