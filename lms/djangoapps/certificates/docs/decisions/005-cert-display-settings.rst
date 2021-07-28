Certificate Display Settings
============================

Status
------
Accepted

Background
----------
Courses have three settings that directly affect certificates visibility. These three settings were all built separately to handle specific use cases and haven't interacted in a quickly understood or consistent manner. These settings are:

``certificate_display_date``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A date at which a certificate can be shown to the learner. Defaulted to two days after course end.

``certificates_display_behavior``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A string that determines when the learner is able to see details about their certificate. This had no option validation and strings were all hardcoded throughout the platform. The three options were ``end``, ``early_no_info``, ``early_with_info``.

``certificates_show_before_end``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A string boolean that determines if the leaner is able to see their certificate before the course ends. It is deprecated but still used to determine if the learner should be shown the certificate

Decision
--------
We are choosing to re-imagine the first two of these existing settings, and leaving the third one deprecated until future removal. ``certificates_display_behavior`` has been updated to use three constants: ``end``, ``end_with_date``, and ``early_no_info`` that are selectable via a more user friendly worded dropdown in Studio. These settings are only used for instructor-paced courses.

``end`` (Studio: "End date of course"): This will be the default and course certificates will become available to the learner once the course end date is reached.

``early_no_info`` (Studio: "Immediately upon passing"): This will cause the certificates to become available to the learner immediately upon the learner achieving a passing grade in the course.

``end_with_date`` (Studio: "A date after the course end date"): This will not display the learner's certificates until the date set in ``certificate_available_date``. If this option is not chosen, ``certificate_available_date`` will not be visible in Studio, the value will set to None, and the date will not effect any learner certificates.

Mongo Data
~~~~~~~~~~
Since Mongo/modulestore data can be hard to trust (due to the fact that course teams can upload data via XML) and there is no way to complete a migration similar to what we do in Django/RDBMS when we are requiring all data to fit a new paradigm, we had to add a new translation layer when reading from modulestore that validates the fields. Now, when a CourseOverview model or CourseDetails object is built with modulestore data, the ``certificate_available_date`` and ``certificates_display_behavior`` fields will be translated to valid combinations. This **does not** write the updated data back into modulestore. It simply takes possibly bad modulestore data and presents the rest of the codebase functional data.

The rules are thus:
1. If ``certificates_display_behavior`` is set to ``early_no_info`` the ``certificate_available_date`` will be ``None``.
2. If the ``certificate_available_date`` is set and the ``certificates_display_behavior`` isn't ``early_no_info``, the ``certificates_display_behavior`` will be changed to ``end_with_date``
3. If neither of those are true, the ``certificate_available_date`` will be set to ``None`` and the ``certificates_display_behavior`` will be set to ``end``

This results in the following translation table:

For brevity:

CAD = ``certificate_available_date``

CDB = ``certificates_display_behavior``


.. list-table:: Translation Table
    :header-rows: 1

    * - CAD in modulestore
      - CDB in modulestore
      - Validated CAD
      - Validated CDB

    * - <date>
      - "end"
      - <date>
      - "end_with_date"

    * - <date>
      - "end_with_date"
      - <date>
      - "end_with_date"

    * - <date>
      - "early_no_info"
      - null
      - "early_no_info"

    * - <date>
      - <some invalid option>
      - <date>
      - "end_with_date"

    * - null
      - "end"
      - null
      - "end"

    * - null
      - "end_with_date"
      - null
      - "end"

    * - null
      - "early_no_info"
      - null
      - "early_no_info"

    * - null
      - <some invalid option>
      - null
      - "end"
