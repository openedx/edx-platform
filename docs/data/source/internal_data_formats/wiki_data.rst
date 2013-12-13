##############################
Wiki Data
##############################

The following sections detail how edX stores Wiki data internally, and is useful for developers and researchers who are examining database exports. 

EdX currently uses an external application called Django Wiki for Wiki functionality within courses. 



****************
article
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
     * - current_revision
       - int(11)
       - NO
       - 
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
       - NO
       - Foreign
     * - group_read
       - boolean
       - NO
       - 
     * - group_write
       - boolean
       - NO
       - 
     * - other_read
       - boolean
       - NO
       - 
     * - other_write
       - boolean
       - NO
       - 


`id`
----
  The primary key. 
  

`current_revision_id`
----------
   The ID of the revision that is displayed for this article.


`created`
------------
    The date the article was created.


`modified`
------------
    The date the article was last modified.
    
`owner_id`
------------
    The user ID of the article owner.
    
`group_read`
------------
    Whether the group has read access to the article.

`group_write`
------------
    Whether the group has write access to the article.

`other_read`
------------
    Whether others have read access to the article.

`other_write`
------------
    Whether others have read access to the article.





****************
article_revision
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
     * - revision_number
       - int(11)
       - NO
       - 
     * - user_message
       - varchar(255)
       - YES
       -
     * - automatic_log
       - varchar(255)
       - YES
       -
     * - ip_address
       - ??
       - YES
       - 
     * - user_id_modified
       - int(11)
       - NO
       - 
     * - created
       - datetime
       - NO
       - 
     * - previous_revision_id
       - int(11)
       - NO
       - Foreign
     * - deleted
       - boolean
       - NO
       - 
     * - locked
       - boolean
       - NO
       - 
     * - article_id
       - int(11)
       - NO
       - Foreign
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
----------
   The ID of the revision.


`user_message`
------------
    The message the user added when saving the revision.


`automatic_log`
------------
    ???
    
`user`
------------
    The ID of the user who made the revision.


`modified`
------------
    The date the article was last modified.
    

`created`
------------
    The date the article was created.


`previous_revision`
------------
    The ID of the revision previous to this one.

`deleted`
------------
    Whether or not the revision was deleted.


`locked`
------------
    Whether or not the revision is locked.
    
`article_id`
----------
   The ID of the revision that is displayed for this article.


`content`
------------
    The content of the article revision.
    
`title`
----------
   The title of the article revision.


