"""
Certificates Data

This provides Data models to represent Certificates data.
"""


class CertificateStatuses:
    """
    Enum for certificate statuses.

    Not all of these statuses are currently used. Some are kept for historical reasons and because existing course
    certificates may have been granted that status.

    audit_notpassing    - User is in the audit track and has not achieved a passing grade.
    audit_passing       - User is in the audit track and has achieved a passing grade.
    deleted             - The PDF certificate has been deleted.
    deleting            - A request has been made to delete the PDF certificate.
    downloadable        - The user has been granted this certificate and the certificate is ready and available.
    error               - An error occurred during PDF certificate generation.
    generating          - A request has been made to generate a PDF certificate, but it has not been generated yet.
    honor_passing       - User is in the honor track and has achieved a passing grade.
    invalidated         - Certificate is not valid.
    notpassing          - The user has not achieved a passing grade.
    requesting          - A request has been made to generate the PDF certificate.
    restricted          - The user is restricted from receiving a certificate.
    unavailable         - Certificate has been invalidated.
    unverified          - The user does not have an approved, unexpired identity verification.

    The following statuses are set by the current course certificates code:
      downloadable - See generation.py
      notpassing - See GeneratedCertificate.mark_notpassing()
      unavailable - See GeneratedCertificate.invalidate()
      unverified - See GeneratedCertificate.mark_unverified()
    """
    deleted = 'deleted'
    deleting = 'deleting'
    downloadable = 'downloadable'
    error = 'error'
    generating = 'generating'
    notpassing = 'notpassing'
    restricted = 'restricted'
    unavailable = 'unavailable'
    auditing = 'auditing'
    audit_passing = 'audit_passing'
    audit_notpassing = 'audit_notpassing'
    honor_passing = 'honor_passing'
    unverified = 'unverified'
    invalidated = 'invalidated'
    requesting = 'requesting'

    readable_statuses = {
        downloadable: "already received",
        notpassing: "didn't receive",
        error: "error states",
        audit_passing: "audit passing states",
        audit_notpassing: "audit not passing states",
    }

    PASSED_STATUSES = (downloadable, generating)
    NON_REFUNDABLE_STATUSES = (downloadable, generating, unavailable)

    @classmethod
    def is_passing_status(cls, status):
        """
        Given the status of a certificate, return a boolean indicating whether
        the student passed the course.
        """
        return status in cls.PASSED_STATUSES

    @classmethod
    def is_refundable_status(cls, status):
        """
        Given the status of a certificate, check to see if that certificate status can
        be refunded.

        Arguments:
            status (str): The status of the certificate that you are checking

        Returns:
            bool: True if the status is refundable.
        """
        return status not in cls.NON_REFUNDABLE_STATUSES
