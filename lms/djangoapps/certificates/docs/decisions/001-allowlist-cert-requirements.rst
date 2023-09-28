Allowlist Course Certificate Requirements
=========================================

Status
------
Accepted

Background
----------
This doc covers requirements for allowlist course certificates.

Users can earn a course certificate in a particular course run (the certificate
is stored in the *GeneratedCertificate* model). If a user has not earned a certificate
but the course staff would like them to have a certificate anyway, the user can
be added to the certificate allowlist for the course run.

The allowlist is stored in the *CertificateAllowlist* model. It was previously
referred to as the certificate whitelist, and was previously stored in the
*CertificateWhitelist* model.

Requirements
------------
Even if a user is on the allowlist for a given course run, they won't necessarily
receive a course certificate in the *downloadable* state. In other words, the user
won't necessarily have a course certificate available to them. To receive a
downloadable allowlist course certificate, the following things must be true at
the time the certificate is generated:

* The user must have an enrollment in the course run

  * The enrollment mode must be eligible for a certificate
  * The enrollment does not need to be active

* The user must not have an invalidated certificate for the course run (see the *CertificateInvalidation* model)
* HTML (web) certificates must be globally enabled, and also enabled for the course run
* The user must be on the allowlist for the course run (see the *CertificateAllowlist* model)
* If the `ENABLE_CERTIFICATES_IDV_REQUIREMENT` WaffleFlag is enabled, a user must have an approved and unexpired ID verification.
