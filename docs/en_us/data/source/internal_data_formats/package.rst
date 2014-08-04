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

An alternative option for event data is available. The
``{date}-{org}-tracking.tar`` file is available each week. It contains a
cumulative log of events in all of an organization's courses. Data for courses
running on both the edx.org and edge.edx.org sites is included in this file.

.. remove this paragraph ^ when weekly file is removed.

.. important:: The ``{org}-{site}-events-{date}.log.gz.gpg`` file is designed to replace the ``{date}-{org}-tracking.tar`` file. Both files will be produced for several weeks, and then production of the ``{date}-{org}-tracking.tar`` file will be discontinued.

.. remove this paragraph ^ when weekly file is removed.

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
  snapshot. It also contains the weekly ``{date}-{org}-tracking.tar`` file of
  cumulative course event data (until production of this file is discontinued).

.. remove the last sentence ^ when weekly event file is removed.

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

.. note:: If you are using a third-party tool to connect to Amazon S3, you may not be able to navigate from one edX bucket to the other in a single session. You may need to disconnect from Amazon S3 and then reconnect to the other bucket.

#. To download a weekly database data file or cumulative event file, connect to
   the edX **course-data** bucket on Amazon S3 using the AWS Command Line
   Interface or a third-party tool.

.. revise this sentence ^ when weekly event logs are no longer available

   For information about providing your credentials to connect to Amazon S3,
   see :ref:`Access Amazon S3`.

2. Download the ``{org}-{date}.zip`` database data file from the **course-
   data** bucket.

   The **course-data** bucket also contains the weekly, cumulative
   ``{date}-{org}-tracking.tar`` files.

.. remove this step ^ when weekly event logs are no longer available

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

.. remove this section v through the next note when weekly file is removed

============================================================
Extracted Contents of ``{date}-{org}-tracking.tar``
============================================================

The ``{date}-{org}-tracking.tar`` file contains cumulative event data for all
of an organization's courses, running on both edx.org and edge.edx.org.

.. note:: Over time, these cumulative files could become large (25GB and larger) and difficult for many data czars to download without encountering session timeouts and other problems. As a result, this file will be superseded by daily ``{org}-{site}-events-{date}.log.gz.gpg`` files in the **edx-course-data** bucket.

After you download the ``{date}-{org}-tracking.tar`` file for your
institution, you:

#. Extract the contents of the downloaded .tar file.

   To balance the load of traffic to edX courses, every course is served by
   multiple edX servers. A different set of servers handles traffic for the two
   edX sites: edx.org ("prod") and edge.edx.org ("edge"). When you extract the
   contents of this file, a separate subdirectory is created for events that
   took place on each edX server.

   For example, subdirectories with these names can be created:

   ``prod-edx-001/``

   ``prod-edx-002/``

   ``prod-edx-003/``

   ``prod-edge-001/``

   ``prod-edge-002/``

   The subdirectory names identify the site on which events took place.

   Each of these subdirectories contains an encrypted log file of event data
   for every day that events occurred on that server. These event tracking data
   files are named ``{date}-{org}.log.gpg``.

2. Use your private key to decrypt the extracted log files. See :ref:`Decrypt
   an Encrypted File`.

.. note:: During analysis, you must combine events from different servers to get a complete picture of the activity in each course. 

.. remove this section ^ when weekly file is removed

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