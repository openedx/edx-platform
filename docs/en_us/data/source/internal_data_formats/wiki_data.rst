.. _Wiki_Data:

##############################
Wiki Data
##############################

The following sections detail how edX stores wiki data internally, and is useful for developers and researchers who are examining database exports. 

EdX currently uses an external application called django-wiki for wiki functionality within courses. 

In the data package, wiki data is delivered in two SQL files: 

* The wiki_article file is a container for each article that is added to the wiki. The full name of this file also includes the organization and course, and indicates a source of either prod (edX) or edge, in this format: edX-*organization*-*course*-wiki_article-*source*-analytics.sql. 

* The wiki_articlerevision file stores data about the articles, including data about changes and deletions. The full name of this file is in this format: edX-*organization*-*course*-wiki_articlerevision-*source*-analytics.sql.

.. _wiki_article:

***********************************
Fields in the wiki_article file
***********************************

The header row of the wiki_article SQL file, and a row of sample data, follow.

.. code-block:: json

    id  current_revision_id created modified  owner_id  group_id  group_read  group_write 
    other_read  other_write

    1437  29819 2013-07-17 21:53:57 2014-01-26 14:48:02 NULL  NULL  1 1 1 1 

The table that follows provides a reference to each field in this file. A description of each field follows the table.

+-----------------------+--------------------+--------------+--------------+
| Field                 | Type               | Null         | Key          |
+=======================+====================+==============+==============+
| id                    | int(11)            | NO           | PRI          |
+-----------------------+--------------------+--------------+--------------+
| current_revision_id   | int(11)            | NO           | UNI          |
+-----------------------+--------------------+--------------+--------------+
| created               | datetime           | NO           |              |
+-----------------------+--------------------+--------------+--------------+
| modified              | datetime           | NO           |              |
+-----------------------+--------------------+--------------+--------------+
| owner_id              | int(11)            | YES          | MUL          |
+-----------------------+--------------------+--------------+--------------+
| group_id              | int(11)            | YES          | MUL          |
+-----------------------+--------------------+--------------+--------------+
| group_read            | tinyint(1)         | NO           |              |
+-----------------------+--------------------+--------------+--------------+
| group_write           | tinyint(1)         | NO           |              |
+-----------------------+--------------------+--------------+--------------+
| other_read            | tinyint(1)         | NO           |              |
+-----------------------+--------------------+--------------+--------------+
| other_write           | tinyint(1)         | NO           |              |
+-----------------------+--------------------+--------------+--------------+

id
----
  The primary key. 
  
current_revision_id
------------------------------
   The ID of the revision that displays for this article.

created
------------
    The date the article was created.

modified
------------
    The date the article properties were last modified.
    
owner_id
------------
    The owner of the article, usually the creator. The owner always has both read and write access.
    
group_id
------------
    As in a UNIX file system, permissions can be given to a user according to group membership. 
    Groups are handled through the Django authentication system.
    
group_read
------------
    Defines whether the group has read access to the article. 1 if so, 0 if not.

group_write
--------------
    Defines whether the group has write access to the article. 1 if so, 0 if not.

other_read
------------
    Defines whether others have read access to the article. 1 if so, 0 if not.

other_write
----------------------
    Defines whether others have write access to the article. 1 if so, 0 if not.

.. _wiki_articlerevision:

******************************************************
Fields in the wiki_articlerevision file 
******************************************************

The header row of the wiki_articlerevision SQL file, and a row of sample data, follow.

.. code-block:: json

    id  revision_number user_message  automatic_log ip_address  user_id modified  created 
    previous_revision_id  deleted locked  article_id  content title
    
    17553 1 Course page automatically created.    NULL  NULL  2013-07-17 21:53:57 2013-07-17 
    21:53:57 NULL  0 0 1437  This is the wiki for edX's edX Demonstration Course.  DemoX

The table that follows provides a reference to the characteristics of each field in this file. Descriptions of the fields follow the table. 

.. list-table::
     :widths: 15 15 10 10
     :header-rows: 1

     * - Field
       - Type
       - Null
       - Key
     * - id
       - int(11) 
       - NO
       - PRI
     * - revision_number
       - int(11)
       - NO
       - 
     * - user_message
       - longtext
       - NO
       -
     * - automatic_log
       - longtext
       - NO
       -
     * - ip_address
       - char(15)
       - YES
       - 
     * - user_id
       - int(11)
       - YES
       - MUL
     * - modified
       - datetime
       - NO
       - 
     * - created
       - datetime
       - NO
       - 
     * - previous_revision_id
       - int(11)
       - YES
       - MUL
     * - deleted
       - tinyint(1)
       - NO
       - 
     * - locked
       - tinyint(1)
       - NO
       - 
     * - article_id
       - int(11)
       - NO
       - MUL
     * - content
       - longtext
       - NO
       - 
     * - title
       - varchar(512)
       - NO
       - 
     
id
----
   The primary key. 

revision_number
--------------------
    The ID of the revision.

user_message
----------------------
    The message the user added when saving the revision.

automatic_log
----------------------
    Some changes to wiki pages are logged to make the revision history for an article available in the user interface.

ip_address
----------------------
    The IP address of the device where the revision was made.

user_id
------------
    The ID of the user who made the revision.

modified
------------
    The date the article was last modified.
    
created
------------
    The date the article was created.

previous_revision_id
----------------------
    The ID of the revision previous to this one.

deleted
------------
    Defines whether the revision was deleted.

locked
------------
    Defines whether the revision is locked.
    
article_id
--------------------
   The ID of the revision that displays data for this article.

content
------------
    The content of the article revision.
    
title
----------
   The title of the article revision.


