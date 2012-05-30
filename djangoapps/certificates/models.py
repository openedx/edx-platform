from django.contrib.auth.models import User
from django.db import models


'''
When a certificate is generated, a unique ID is generated so that 
the certificate can be verified later. The ID is a UUID4, so that
it can't be easily guessed and so that it is unique. Even though
we save these generated certificates (for later verification), we
also record the UUID so that if we regenerate the certificate it
will have the same UUID.

Certificates are created for a student and an offering of a course.

'''

class GeneratedCertificate(models.Model):
    user = models.ForeignKey(User, db_index=True)
    certificate_id = models.CharField(max_length=32)
    
    download_url = models.CharField(max_length=128, null=True)