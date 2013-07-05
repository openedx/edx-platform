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
        randnum = random.randint(0,6)
        print randnum
        print "test"
        if randnum == 0:
            raise SMTPResponseException(235, "Auth Successful")
        elif randnum == 1:
            raise SMTPResponseException(250, "Successful Delivery")
        elif randnum == 2:
            raise SMTPResponseException(535, "Auth Cred Invalid")
        elif randnum == 3:
            raise SMTPResponseException(530, "Auth required")
        elif randnum == 4:
            raise SMTPResponseException(554, "Message rejection")
        elif randnum == 5:
            raise SMTPResponseException(454, "Max Send Rate exceeded")
        else:
            print "Success!"
        pass

if __name__ == "__main__":
    smtp_server = FakeSMTPServer(('localhost', 1025), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
