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

Certificates are generated in batches by a cron job, when a
certificate is available for download the GeneratedCertificate
table is updated with information that will be displayed
on the course overview page.


'''


class GeneratedCertificate(models.Model):
    user = models.ForeignKey(User)
    course_id = models.CharField(max_length=255, default=False)
    certificate_id = models.CharField(max_length=32, default=False)
    graded_certificate_id = models.CharField(max_length=32, default=False)

    download_url = models.CharField(max_length=128, default=False)
    graded_download_url = models.CharField(max_length=128, default=False)
    grade = models.CharField(max_length=5, default=False)
    key = models.CharField(max_length=32, default=False)

    # enabled should only be true if the student has earned a passing grade
    # in the course.
    enabled = models.BooleanField(default=False)


def certificate_state_for_student(student):
    '''
    This returns a dictionary with a key for state, and other information.
    The state is one of the following:

    unavailable  - A student is not eligible for a certificate.
    generating   - A student has requested a certificate,
                   but it is not generated yet.
    downloadable - The certificate has been requested and is
                   available for download.

    If the state is "downloadable", the dictionary also contains
    "download_url" and "graded_download_url".

    '''

    try:
        generated_certificate = GeneratedCertificate.objects.get(
                user=student)
        if generated_certificate.enabled:
            if generated_certificate.download_url:
                return {
                      'state': 'downloadable',
                      'download_url':
                        generated_certificate.download_url,
                      'graded_download_url':
                        generated_certificate.graded_download_url
                       }
            else:
                return {'state': 'generating'}
        else:
            # If enabled=False, there is no certificate available
            # Our output will be the same as if the
            # GeneratedCertificate did not exist
            pass
    except GeneratedCertificate.DoesNotExist:
        pass
    return {'state': 'unavailable'}
