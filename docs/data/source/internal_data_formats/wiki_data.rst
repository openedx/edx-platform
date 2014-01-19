##############################
Wiki Data
##############################

The following sections detail how edX stores Wiki data internally, and is useful for developers and researchers who are examining database exports. 

EdX currently uses an external application called Django Wiki for Wiki functionality within courses. 



****************
wiki_article
****************

  .. list-table::
     :widths: 15 15 15 15
     :header-rows: 1

     * - Field
       - Type
       - Null
       - Key
     * - id
       - int(11) 
       - NO
       - PRI
     * - current_revision_id
       - int(11)
       - NO
       - UNI
     * - created
       - datetime
       - NO
       -
     * - modified
       - datetime
       - NO
       -
     * - owner_id
       - int(11)
       - YES
       - MUL
     * - group_id
       - int(11)
       - YES
       - MUL
     * - group_read
       - tinyint(1)
       - NO
       - 
     * - group_write
       - tinyint(1)
       - NO
       - 
     * - other_read
       - tinyint(1)
       - NO
       - 
     * - other_write
       - tinyint(1)
       - NO
       - 


`id`
----
  The primary key. 
  

`current_revision_id`
------------------------------
   The ID of the revision that is displayed for this article.


`created`
------------
    The date the article was created.


`modified`
------------
    The date the article properties were last modified.
    
`owner_id`
------------
    The owner of the article, usually the creator. The owner always has both read and write access.
    
`group_id`
------------
    As in a UNIX file system, permissions can be given to a user according to group membership. 
    Groups are handled through the Django auth system.
    
`group_read`
------------
    Whether the group has read access to the article.

`group_write`
--------------
    Whether the group has write access to the article.

`other_read`
------------
    Whether others have read access to the article.

`other_write`
----------------------
    Whether others have read access to the article.





**********************
wiki_articlerevision
**********************

  .. list-table::
     :widths: 15 15 15 15
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
     


`id`
----
  The primary key. 


`revision_number`
--------------------
   The ID of the revision.


`user_message`
----------------------
    The message the user added when saving the revision.


`automatic_log`
----------------------

    
`user_id`
------------
    The ID of the user who made the revision.


`modified`
------------
    The date the article was last modified.
    

`created`
------------
    The date the article was created.


`previous_revision_id`
----------------------
    The ID of the revision previous to this one.

`deleted`
------------
    Whether or not the revision was deleted.


`locked`
------------
    Whether or not the revision is locked.
    
`article_id`
--------------------
   The ID of the revision that is displayed for this article.


`content`
------------
    The content of the article revision.
    
`title`
----------
   The title of the article revision.


