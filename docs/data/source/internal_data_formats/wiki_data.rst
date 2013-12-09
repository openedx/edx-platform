##############################
Wiki Data
##############################

The following sections detail how edX stores Wiki data internally, and is useful for developers and researchers who are examining database exports. This information includes demographic information collected at signup, course enrollment, course progress, and certificate status.

Conventions to keep in mind:

* edX currently uses an external application called Django Wiki for Wiki functionality within courses. 


All of our tables will be described below, first in summary form with field types and constraints, and then with a detailed explanation of each field. For those not familiar with the MySQL schema terminology in the table summaries:

`Type`
  This is the kind of data it is, along with the size of the field. When a numeric field has a length specified, it just means that's how many digits we want displayed -- it has no affect on the number of bytes used.

  .. list-table::
     :widths: 10 80
     :header-rows: 1

     * - Value
       - Meaning
     * - `int`
       - 4 byte integer.
     * - `smallint`
       - 2 byte integer, sometimes used for enumerated values.
     * - `tinyint`
       - 1 byte integer, but usually just used to indicate a boolean field with 0 = False and 1 = True.
     * - `varchar`
       - String, typically short and indexable. The length is the number of chars, not bytes (so unicode friendly).
     * - `longtext`
       - A long block of text, usually not indexed.
     * - `date`
       - Date
     * - `datetime`
       - Datetime in UTC, precision in seconds.

`Null`

  .. list-table::
     :widths: 10 80
     :header-rows: 1

     * - Value
       - Meaning
     * - `YES`
       - `NULL` values are allowed
     * - `NO`
       - `NULL` values are not allowed

  .. note::
     Django often just places blank strings instead of NULL when it wants to indicate a text value is optional. This is used more meaningful for numeric and date fields.

`Key`
  .. list-table::
     :widths: 10 80
     :header-rows: 1

     * - Value
       - Meaning
     * - `PRI`
       - Primary key for the table, usually named `id`, unique
     * - `UNI`
       - Unique
     * - `MUL`
       - Indexed for fast lookup, but the same value can appear multiple times. A Unique index that allows `NULL` can also show up as `MUL`.


****************
Notification Type
****************

The `notifications` table stores . It has the following fields::

  +------------------------------+--------------+------+-----+
  | Field                        | Type         | Null | Key |
  +------------------------------+--------------+------+-----+
  | key                          | varchar(128) | NO   | PRI |
  | label                        | varchar(128) | YES  |     |
  | content_type                 | ForeignKey   | YES  |     | 
  +------------------------------+--------------+------+-----+

`key`
----
  Primary key . . .  

`label`
----------
   The label for the notification . . .

`content_type`
------------
    A foreign key . . .



****************
Settings
****************

The `Settings` table stores . It has the following fields::

  +------------------------------+--------------+------+-----+
  | Field                        | Type         | Null | Key |
  +------------------------------+--------------+------+-----+
  | user                         | ForeignKey   | NO   | PRI |
  | interval                     | smallint(6)  | NO   |     |
  +------------------------------+--------------+------+-----+

`user`
----
  Primary key . . .  

`interval`
----------
   The . . . 


****************
Subscriptions
****************

The `Subscriptions` table stores . It has the following fields::

  +------------------------------+--------------+------+-----+
  | Field                        | Type         | Null | Key |
  +------------------------------+--------------+------+-----+
  | settings                     | ForeignKey   | NO   | PRI |
  | notification_type            | ForeignKey   | NO   |     |
  | object_id                    | varchar(64)  | YES  |     |
  | send_emails                  | boolean      | NO   |     |  
  +------------------------------+--------------+------+-----+

`settings`
----
  Primary key . . .  

`notification type`
----------
   The . . . 
   
`object_id`
----
  Primary key . . .  

`send_emails`
----------
   The . . . 
   
   
****************
Notification
****************

The `Notification` table stores . It has the following fields::

  +------------------------------+--------------+------+-----+
  | Field                        | Type         | Null | Key |
  +------------------------------+--------------+------+-----+
  | subscription                 | ForeignKey   | NO   | PRI |
  | message                      | text         | NO   |     |
  | url                          | URLField     | YES  |     |
  | is_viewed                    | boolean      | NO   |     |  
  | is_emailed                   | boolean      | NO   |     |  
  | created                      | datetime     | NO   |     |  
  +------------------------------+--------------+------+-----+

`subscription`
----
  Primary key . . .  

`message`
----------
   The . . . 
   
`url`
----
  Primary key . . .  

`is_viewed`
----------
   The . . . 

`is_emailed`
----------
   The . . . 

`created`
----------
   The . . . 
