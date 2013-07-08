import smtpd
import asyncore
import random
import smtplib

class FakeSMTPServer(smtpd.SMTPServer):
    """A fake SMTP server"""
    def __init__(*args, **kwargs):
        print "Running fake smtp server on port 1025"
        smtpd.SMTPServer.__init__(*args, **kwargs)
    
    def set_errtype(self, e, c):
        self.errtype = e
        self.code = c

    def process_message(*args, **kwargs):
        if errtype == "DATA":
            raise SMTPDataError(code, "Data Error")
        elif errtype == "CONNECT":
            raise SMTPConnectError(code, "Connect Error")
        elif errtype == "SERVERDISCONNECT":
            raise SMTPServerDisconnected(code, "Server Disconnected")
        else:
            print "Success!"
        pass

if __name__ == "__main__":
    smtp_server = FakeSMTPServer(('localhost', 1025), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
