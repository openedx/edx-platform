====================================
Bulk Email HTML Content Sanitization
====================================

Status
------

Accepted

Background
----------

The Bulk Course Email tool allows course teams to author messages that can be sent to learners and supporting staff enrolled in their courses. An editor is provided as part of the tool for authoring these email messages. If desired, the editor allows advanced users to write custom raw HTML in the message.

It is considered good security practice to scan and sanitize user-provided content before storing or using the data.

Decision
--------

We will sanitize the HTML content received through the bulk course email tool before sending the messages to any recipients.

We will use the `bleach`_ Python package to sanitize the data.

We will introduce a new configuration setting called ``BULK_COURSE_EMAIL_ALLOWED_HTML_TAGS`` that acts as an *allowlist* of HTML tags permitted for use within the body of a message authored by the bulk course email tool. A default list of options is provided in the ``lms/envs/common.py`` `configuration file`_. Offending data will be escaped (converted to plaintext) over being stripped out.

Consequences
------------

A message sent through the Bulk Course Email tool that includes any restricted HTML content will not appear as intended to the recipients of the message. The restricted HTML content will be converted to plaintext and will not render.

.. _bleach: https://bleach.readthedocs.io/en/latest/
.. _configuration file: https://github.com/openedx/edx-platform/blob/e608db847c39c2e3d723ef81f7dac66f63663a28/lms/envs/common.py#L4965
