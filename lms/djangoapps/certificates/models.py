from django.contrib.auth.models import User
from django.db import models
from datetime import datetime

'''
Certificates are created for a student and an offering of a course.

When a certificate is generated, a unique ID is generated so that
the certificate can be verified later. The ID is a UUID4, so that
it can't be easily guessed and so that it is unique.

Certificates are generated in batches by a cron job, when a
certificate is available for download the GeneratedCertificate
table is updated with information that will be displayed
on the course overview page.


State diagram:

[deleted,error,unavailable] [error,downloadable]
            +                +             +
            |                |             |
            |                |             |
         add_cert       regen_cert     del_cert
            |                |             |
            v                v             v
       [generating]    [regenerating]  [deleting]
            +                +             +
            |                |             |
       certificate      certificate    certificate
         created       removed,created   deleted
            +----------------+-------------+------->[error]
            |                |             |
            |                |             |
            v                v             v
      [downloadable]   [downloadable]  [deleted]

'''


class CertificateStatuses(object):
    unavailable = 'unavailable'
    generating = 'generating'
    regenerating = 'regenerating'
    deleting = 'deleting'
    deleted = 'deleted'
    downloadable = 'downloadable'
    error = 'error'


class GeneratedCertificate(models.Model):
    user = models.ForeignKey(User)
    course_id = models.CharField(max_length=255, blank=True, default='')
    verify_uuid = models.CharField(max_length=32, blank=True, default='')
    download_uuid = models.CharField(max_length=32, blank=True, default='')
    download_url = models.CharField(max_length=128, blank=True,  default='')
    grade = models.CharField(max_length=5, blank=True, default='')
    key = models.CharField(max_length=32, blank=True, default='')
    distinction = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default='unavailable')
    name = models.CharField(blank=True, max_length=255)
    created_date = models.DateTimeField(
            auto_now_add=True, default=datetime.now)
    modified_date = models.DateTimeField(
            auto_now=True, default=datetime.now)

    class Meta:
        unique_together = (('user', 'course_id'),)


def certificate_status_for_student(student, course_id):
    '''
    This returns a dictionary with a key for status, and other information.
    The status is one of the following:

    unavailable  - A student is not eligible for a certificate.
    generating   - A request has been made to generate a certificate,
                   but it has not been generated yet.
    regenerating - A request has been made to regenerate a certificate,
                   but it has not been generated yet.
    deleting     - A request has been made to delete a certificate.

    deleted      - The certificate has been deleted.
    downloadable - The certificate is available for download.

    If the status is "downloadable", the dictionary also contains
    "download_url".

    '''

    try:
        generated_certificate = GeneratedCertificate.objects.get(
                user=student, course_id=course_id)
        if generated_certificate.status == CertificateStatuses.downloadable:
            return {
                      'status': CertificateStatuses.downloadable,
                      'download_url': generated_certificate.download_url,
                   }
        else:
            return {'status': generated_certificate.status}
    except GeneratedCertificate.DoesNotExist:
        pass
    return {'status': 'unavailable'}
