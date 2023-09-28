=============================================
Bulk Email HTML Content Will Not Be Sanitized
=============================================

Status
------

Accepted

Background
----------

The Bulk Course Email tool allows course teams to author messages that can be sent to learners and supporting staff enrolled in their courses. An editor is provided as part of the tool for authoring these email messages. If desired, the editor allows advanced users to write custom raw HTML in the message.

It is considered good security practice to scan and sanitize user-provided content before storing or using the data.

Decision
--------

We will not sanitize the HTML content received through the bulk course email tool on the back end. The content that instructors create for courses also allows unfiltered html, which is arguably a larger risk than email, which will block the execution of certain types of code. In the future, if a standard is set for filtering course content, the same standard could be applied here.


Rejected solutions
------------------

Bleach with allowlist
*********************

It has been standard practice for us to use `Bleach`_ with an allowlist to sanitize user provided content within the Open edX ecosystem. Santization using blocklists is vulnerable to obfuscation attacks, and the industry standard is to use an allowlist and explicitly enumerate all supported values. Given that this tool has been live for many years with no sanitization in place, a highly restrictive allowlist would be difficult to roll out to users, resulting in broken email templates and angry instructors who are used to having free rein. A permissive allowlist would potentially address this, but presents the non-trivial problem of assembling and maintaining a comprehensive list.

.. _bleach: https://bleach.readthedocs.io/en/latest/
