.. _Package:

######################################
Data Delivered in Data Packages
######################################

For partners who are running courses on edx.org and edge.edx.org, edX regularly
makes research data available for download from the Amazon S3 storage service.
The *data package* that data czars download from Amazon S3 consists of a set of
compressed and encrypted files that contain event logs and database snapshots
for all of their organizations' edx.org and edge.edx.org courses.

* :ref:`Data Package Files`

* :ref:`Amazon S3 Buckets and Directories`

* :ref:`Download Data Packages from Amazon S3`

* :ref:`Data Package Contents`

Course-specific data is also available to the members of individual course
teams. Users who are assigned the Instructor or Course Staff role can view and
download data from the Instructor Dashboard in their live courses and from edX
Insights. The data available to course teams from these applications is a
subset of the data available in the data packages. For more information, see
`Building and Running an edX Course`_ and `Using edX Insights`_.

.. _Data Package Files:

**********************
Data Package Files
**********************

A data package consists of different files that contain event data and database
data. 

.. note:: In all file names, the date is in {YYYY}-{MM}-{DD} format.

You download these files from different Amazon S3 "buckets". See :ref:`Amazon
S3 Buckets and Directories`.

============
Event Data
============

The ``{org}-{site}-events-{date}.log.gz.gpg`` file contains a daily log of
course events. A separate file is available for courses running on edge.edx.org
(with "edge" for {site} in the file name) and on edx.org (with "edx" for
{site}).

For a partner organization named UniversityX, these daily files are identified
by the organization name, the edX site name, and the date. For example,
``universityx-edge-2014-07-25.log.gz.gpg``.

For information about the contents of these files, see :ref:`Data Package
Contents`.

==================
Database Data
==================

The ``{org}-{date}.zip`` file contains views on database tables. This file
includes data as of the time of the export, for all of an organization's
courses on both the edx.org and edge.edx.org. sites. A new file is available
every week, representing the database at that point in time.

For a partner organization named UniversityX, each weekly file is identified by
the organization name and its extraction date: for example,
``universityx-2013-10-27.zip``.

For information about the contents of this file, see :ref:`Data Package
Contents`.

.. _Amazon S3 Buckets and Directories:

********************************************
Amazon S3 Buckets and Directories
********************************************

Data package files are located in the following buckets on Amazon S3:

* The **edx-course-data** bucket contains the daily
  ``{org}-{site}-events-{date}.log.gz.gpg`` files of course event data.
  
* The **course-data** bucket contains the weekly ``{org}-{date}.zip`` database
  snapshot. 

For information about accessing Amazon S3, see :ref:`Access Amazon S3`.

.. _Download Data Packages from Amazon S3:

****************************************************************
Download Data Packages from Amazon S3
****************************************************************

You download the files in your data package from the Amazon S3 storage service.

==========================
Download Daily Event Files
==========================

#. To download daily event files, use the AWS Command Line Interface or a
   third-party tool to connect to the **edx-course-data** bucket on Amazon S3.

   For information about providing your credentials to connect to Amazon S3,
   see :ref:`Access Amazon S3`.

#. Navigate the directory structure in the **edx-course-data** bucket to locate
   the files that you want:

   ``{org}/{site}/events/{year}``

   The event logs in the ``{year}`` directory are in compressed, encrypted
   files named ``{org}-{site}-events-{date}.log.gz.gpg``.

3. Download the ``{org}-{site}-events-{date}.log.gz.gpg`` file.

   If your organization has courses running on both edx.org and edge.edx.org,
   separate log files are available for the "edx" site and the "edge" site.
   Repeat this step to download the file for the other site.

============================
Download Weekly Files
============================

.. note:: If you are using a third-party tool to connect to Amazon S3, you may 
 not be able to navigate from one edX bucket to the other in a single session.
 You may need to disconnect from Amazon S3 and then reconnect to the other
 bucket.

#. To download a weekly database data file, connect to the edX **course-data**
   bucket on Amazon S3 using the AWS Command Line Interface or a third-party
   tool.

   For information about providing your credentials to connect to Amazon S3,
   see :ref:`Access Amazon S3`.

2. Download the ``{org}-{date}.zip`` database data file from the **course-
   data** bucket.

.. _AWS Command Line Interface: http://aws.amazon.com/cli/

.. _Data Package Contents:

**********************
Data Package Contents
**********************

Each of the files you download contains one or more files of research data.

================================================================
Extracted Contents of ``{org}-{site}-events-{date}.log.gz.gpg``
================================================================

The ``{org}-{site}-events-{date}.log.gz.gpg`` file contains all event data for
courses on a single edX site for one 24-hour period. After you download a
``{org}-{site}-events-{date}.log.gz.gpg`` file for your institution, you:

#. Use your private key to decrypt the file. See :ref:`Decrypt an Encrypted
   File`.

#. Extract the log file from the compressed .gz file. The result is a single
   file named ``{org}-{site}-events-{date}.log``. (Alternatively, the data can
   be decompressed in stream using a tool such as gzip or, related libraries in
   your preferred programming language.)

============================================
Extracted Contents of ``{org}-{date}.zip``
============================================

After you download the ``{org}-{date}.zip`` file for your
institution, you:

#. Extract the contents of the file. When you extract (or unzip) this file, all
   of the files that it contains are placed in the same directory. All of the
   extracted files end in ``.gpg``, which indicates that they are encrypted.

#. Use your private key to decrypt the extracted files. See
   :ref:`Decrypt an Encrypted File`.

The result of extracting and decrypting the ``{org}-{date}.zip`` file is the
following set of sql and mongo database files.

``{org}-{course}-{date}-auth_user-{site}-analytics.sql``

  Information about the users who are authorized to access the course. See
  :ref:`auth_user`.

``{org}-{course}-{date}-auth_userprofile-{site}-analytics.sql``

  Demographic data provided by users during site registration. See
  :ref:`auth_userprofile`.

``{org}-{course}-{date}-certificates_generatedcertificate-{site}-analytics.sql``

  The final grade and certificate status for students (populated after course
  completion). See :ref:`certificates_generatedcertificate`.

``{org}-{course}-{date}-courseware_studentmodule-{site}-analytics.sql``

  The courseware state for each student, with a separate row for each item in
  the course content that the student accesses. No file is produced for courses
  that do not have any records in this table (for example, recently created
  courses). See :ref:`courseware_studentmodule`.

``{org}-{course}-{date}-student_courseenrollment-{site}-analytics.sql``

  The enrollment status and type of enrollment selected by each student in the
  course. See :ref:`student_courseenrollment`.

``{org}-{course}-{date}-user_api_usercoursetag-{site}-analytics.sql``

  Metadata that describes different types of student participation in the
  course. See :ref:`user_api_usercoursetag`.

``{org}-{course}-{date}-user_id_map-{site}-analytics.sql``

   A mapping of user IDs to site-wide obfuscated IDs. See :ref:`user_id_map`.

``{org}-{course}-{date}-{site}.mongo``

  The content and characteristics of course discussion interactions. See
  :ref:`Discussion Forums Data`.

``{org}-{course}-{date}-wiki_article-{site}-analytics.sql``

  Information about the articles added to the course wiki. See
  :ref:`wiki_article`.

``{org}-{course}-{date}-wiki_articlerevision-{site}-analytics.sql``

  Changes and deletions affecting course wiki articles. See
  :ref:`wiki_articlerevision`.



.. _Using edX Insights: http://edx-insights.readthedocs.org/en/latest/
.. _Building and Running an edX Course: http://edx.readthedocs.org/projects/edx-partner-course-staff/en/latest/