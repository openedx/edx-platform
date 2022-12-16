Regular Course Certificate Requirements
=======================================

Status
------
Accepted

Background
----------
This doc covers requirements for regular (non-allowlist) course certificates.

Users can earn a course certificate in a particular course run if they meet a
number of criteria, and the course run is configured to grant them the certificate.
The certificates are stored in the *GeneratedCertificate* model.

Requirements
------------
For a user to receive a course certificate in the *downloadable* state (for the
user to have a course certificate available to them), the following things must
be true at the time the certificate is generated:

* The user must have an enrollment in the course run

  * The enrollment mode must be eligible for a certificate
  * The enrollment does not need to be active

* The user must not have an invalidated certificate for the course run (see the *CertificateInvalidation* model)
* HTML (web) certificates must be globally enabled, and also enabled for the course run
* The user must have passed the course run
* The user must not be a beta tester in the course run
* The course run must not be a CCX (custom edX course)
* If the `ENABLE_CERTIFICATES_IDV_REQUIREMENT` WaffleFlag is enabled, a user must have an approved and unexpired ID verification.
