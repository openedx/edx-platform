from django.contrib.auth.models import User
from django.db import models


'''
Certificates are created for a student and an offering of a course.

When a certificate is generated, a unique ID is generated so that 
the certificate can be verified later. The ID is a UUID4, so that
it can't be easily guessed and so that it is unique. Even though
we save these generated certificates (for later verification), we
also record the UUID so that if we regenerate the certificate it
will have the same UUID.

If certificates are being generated on the fly, a GeneratedCertificate
should be created with the user, certificate_id, and enabled set 
when a student requests a certificate. When the certificate has been
generated, the download_url should be set.

Certificates can also be pre-generated. In this case, the user,
certificate_id, and download_url are all set before the user does
anything. When the user requests the certificate, only enabled
needs to be set to true.

'''

class GeneratedCertificate(models.Model):
    user = models.ForeignKey(User, db_index=True)
    certificate_id = models.CharField(max_length=32)
    
    download_url = models.CharField(max_length=128, null=True)
    
    # enabled should only be true if the student has earned a grade in the course
    # The student must have a grade and request a certificate for enabled to be True
    enabled = models.BooleanField(default=False)