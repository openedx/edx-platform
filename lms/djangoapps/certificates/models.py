from django.conf import settings as settings

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
    # This is the name at the time of request
    name = models.CharField(blank=True, max_length=255)

    certificate_id = models.CharField(max_length=32, null=True, default=None)
    graded_certificate_id = models.CharField(max_length=32, null=True, default=None)

    download_url = models.CharField(max_length=128, null=True)
    graded_download_url = models.CharField(max_length=128, null=True)

    grade = models.CharField(max_length=5, null=True)

    # enabled should only be true if the student has earned a grade in the course
    # The student must have a grade and request a certificate for enabled to be True
    enabled = models.BooleanField(default=False)


class RevokedCertificate(models.Model):
    """
    This model is for when a GeneratedCertificate must be regenerated. This model
    contains all the same fields, to store a record of what the GeneratedCertificate
    was before it was revoked (at which time all of it's information can change when
    it is regenerated).

    GeneratedCertificate may be deleted once they are revoked, and then created again.
    For this reason, the only link between a GeneratedCertificate and RevokedCertificate
    is that they share the same user.
    """
    ####-------------------New Fields--------------------####
    explanation = models.TextField(blank=True)

    ####---------Fields from GeneratedCertificate---------####
    user = models.ForeignKey(User, db_index=True)
    # This is the name at the time of request
    name = models.CharField(blank=True, max_length=255)

    certificate_id = models.CharField(max_length=32, null=True, default=None)
    graded_certificate_id = models.CharField(max_length=32, null=True, default=None)

    download_url = models.CharField(max_length=128, null=True)
    graded_download_url = models.CharField(max_length=128, null=True)

    grade = models.CharField(max_length=5, null=True)

    enabled = models.BooleanField(default=False)


def revoke_certificate(certificate, explanation):
    """
    This method takes a GeneratedCertificate. It records its information from the certificate
    into a RevokedCertificate, and then marks the certificate as needing regenerating.
    When the new certificiate is regenerated it will have new IDs and download URLS.

    Once this method has been called, it is safe to delete the certificate, or modify the
    certificate's name or grade until it has been generated again.
    """
    revoked = RevokedCertificate(user=certificate.user,
                                    name=certificate.name,
                                    certificate_id=certificate.certificate_id,
                                    graded_certificate_id=certificate.graded_certificate_id,
                                    download_url=certificate.download_url,
                                    graded_download_url=certificate.graded_download_url,
                                    grade=certificate.grade,
                                    enabled=certificate.enabled)

    revoked.explanation = explanation

    certificate.certificate_id = None
    certificate.graded_certificate_id = None
    certificate.download_url = None
    certificate.graded_download_url = None

    certificate.save()
    revoked.save()


def certificate_state_for_student(student, grade):
    '''
    This returns a dictionary with a key for state, and other information. The state is one of the
    following:

    unavailable - A student is not eligible for a certificate.
    requestable - A student is eligible to request a certificate
    generating - A student has requested a certificate, but it is not generated yet.
    downloadable - The certificate has been requested and is available for download.

    If the state is "downloadable", the dictionary also contains "download_url" and "graded_download_url".

    '''

    if grade:
        #TODO: Remove the following after debugging
        if settings.DEBUG_SURVEY:
            return {'state': 'requestable'}

        try:
            generated_certificate = GeneratedCertificate.objects.get(user=student)
            if generated_certificate.enabled:
                if generated_certificate.download_url:
                    return {'state': 'downloadable',
                             'download_url': generated_certificate.download_url,
                             'graded_download_url': generated_certificate.graded_download_url}
                else:
                    return {'state': 'generating'}
            else:
                # If enabled=False, it may have been pre-generated but not yet requested
                # Our output will be the same as if the GeneratedCertificate did not exist
                pass
        except GeneratedCertificate.DoesNotExist:
            pass
        return {'state': 'requestable'}
    else:
        # No grade, no certificate. No exceptions
        return {'state': 'unavailable'}
