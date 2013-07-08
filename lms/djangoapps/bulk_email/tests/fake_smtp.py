"""Taken from internet"""

import smtpd
import asyncore
import random
import smtplib

class FakeSMTPServer(smtpd.SMTPServer):
    """A Fake smtp server"""
    def __init__(*args, **kwargs):
        print "Running fake smtp server on port 1025"
        smtpd.SMTPServer.__init__(*args, **kwargs)
    
    def process_message(*args, **kwargs):
        errtype = raw_input("Enter DATA, CONNECT, or SERVERDISCONNECT: ")
        code = raw_input("Enter the error code: ")
        print "You entered", errtype, code
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
