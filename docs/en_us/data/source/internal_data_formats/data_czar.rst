.. _Data_Czar:

####################################################
Data Czar/Data Team Selection and Responsibilities
####################################################

A data czar is the single representative at a partner institution who has the
credentials to download and decrypt edX data packages. The data czar is
responsible for transferring data securely to researchers and other interested
parties after it is received. Due to the sensitivity of this data, the
responsibility for these activities is restricted to one individual. At each
partner institution, the data czar is the primary point of contact for
information about edX data.

* :ref:`Skills_Experience_Data_Czar`

* :ref:`Resources_Information`

At some institutions, only the data czar works on research projects that use
the course data in edX data packages. At other institutions, the data czar
works with a team of additional contributors, or is responsible only for
making a secure transfer of the data to the research team. Typically, the data
team includes members in the following roles (or a data czar with these skill
sets):

* Database administrators work with the SQL and NoSQL data files and write queries on the data.

* Statisticians and data analysts mine the data.

* Educational researchers pose questions and interpret the results of queries on the data.

See :ref:`Skills_Experience_Contributors`.

All of the individuals who are permitted to access the data should be trained
in, and comply with, their institution's secure data handling protocols.

.. _Skills_Experience_Data_Czar:

**************************************
Skills and Experience of Data Czars
**************************************

The individuals who are selected by a partner institution to be edX data czars
typically have experience working with sensitive student data, are familiar
with encryption/decryption and file transfer protocols, and can validate,
copy, move, and store large files. The data czar is responsible for ensuring
compliance with your institution's and country's regulations with respect to
the sharing of this data.

=====================
General Skills
=====================

- Ability to set up and manage data access.

- Knowledgeable of general data privacy and security best practices.

- Experience with management of sensitive student data.

=====================
Technical Skills
=====================

- Familiarity with PGP and GPG encryption and decryption.

- Ability to download large files from Amazon Web Service (AWS) Simple Storage
  Service (S3).

- Experience working with archive files in TAR, GZ, and ZIP formats.

- Familiarity with SQL and noSQL (Mongo) databases.

- Familiarity with CSV and JSON file formats. 

- Experience copying, moving, and storing large files in bulk.

- Ability to validate the data and files received and distributed.

.. _Resources_Information:

**************************************
Resources and Information
**************************************

The edX Analytics team adds every data czar to a Google Group and mailing
list called `course-data`_.

.. _course-data: http://groups.google.com/a/edx.org/forum/#!forum/course-data

EdX also hosts an `Open edX Analytics wiki`_ that is available to the
public. The wiki provides links to the engineering roadmap, information about
operational issues, and release notes describing past releases.

.. _Open edX Analytics wiki: http://edx-wiki.atlassian.net/wiki/display/OA/Open+edX+Analytics+Home

.. _Skills_Experience_Contributors:

*************************************************
Skills and Experience of Other Contributors
*************************************************

In addition to the data czar, each partner institution assembles a team of
contributors to their research projects. This team can include database
administrators, software engineers, data specialists, and educational
researchers. The team can be large or small, but collectively its members need
to be able to work with SQL and NoSQL databases, write queries, and convert
the data from raw formats into standard research packages, such as CSV files,
spreadsheets, or other desired formats.

=====================
General Skills
=====================

- Attention to detail.

- Experience setting up and testing a data conversion pipeline.

- Ability to identify interesting features in a complex and rich data set.

- Familiarity with anonymization and obfuscation techniques.

- Familiarity with data privacy and security best practices.

- Experience managing sensitive student data.

=====================
Technical Skills
=====================

- Familiarity with CSV, MongoDB, JSON, Unicode, XML, HTML.

- Ability to set up, query, and administer both SQL and noSQL databases. 

- Experience with console/bash scripts.

- Basic or advanced scripting (for example, using Python or Ruby) to convert,
  join, and aggregate data from different data sources, handle JSON
  serialization, and Unicode specificities.

- Experience with data mining and data aggregation across a rich, varied data set.

- Ability to write parsing scripts that properly handle JSON serialization and
  Unicode.
