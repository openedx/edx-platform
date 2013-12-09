##############################
Wiki Data
##############################

The following sections detail how edX stores Wiki data internally, and is useful for developers and researchers who are examining database exports. This information includes demographic information collected at signup, course enrollment, course progress, and certificate status.

Conventions to keep in mind:

* edX currently uses an external application called Django Wiki for Wiki functionality within courses. 



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
