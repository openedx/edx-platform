2. Data Storage
################

Status
******

**Provisional** *2023-09-13*

Context
*******

The requirements of the course roles project indicate that equal priority be given to user understanding of the roles and flexibility of the system. It has been determined that in order to prioritize user understadning of roles and permissions it is necessary that the descriptions be localized.

**Localization:** It is necessary for all text that will be displayed in the LMS to be shown in the appropriate language. The current process for translation requires that all strings displayed to users be in strings in the codebase.

**Flexibility:** It is necessary that course_roles allows for the easy creation of new roles. It is considered important, but not strictly required, that each instance of the Open edX code can have its own roles without needing to fork the repo and maintain separate code. 

Decision
********

We will be using a combination of data storage in the database and data storage structures within the code.
We will store the roles, permissions, role permissions (rolepermission table), and role assignments (userrole table) in the database. 
We will store the role names (for default roles), permission names, and permission descriptions in a data object in the code.
We will write code that pulls the role name from the database table for any role not found in the data object in the code. This applies to non-default roles that may differ from instance to instance.
We will update both the code and the database table rows if a new permission is added.
We will update both the code and the database table rows if a new default row is added.
We will only add data in the database if a role is being added to a single Open edX instance.

Consequences
************

This decision will mean that any futurue default role additions or permissions changes will require changes in the code and the database. It also means that there is a chance of a default role name being listed in the UI using the name value in the database. This would occur if a role was added to the database, but the role was not added to the data structure in the code.

This decision will allow for roles to be added to one instance of Open edX and not others. This can be achieved by adding the role in the database for the instance, but intentionally not adding it in the data object in the code. It is important that the role name added in the database is in the language that it should be displayed in, in the UI, because it will not be translated.

This decision allows the course_roles djangoapp to utilize the same translation processes that are already in use for the codebase, with no changes.

This decision allows the system to utillize database querying functionality to determine the permissions that belong to a role and by association to a user. It benefits from the database's ability to quickly return query results.

Rejected Alternatives
*********************

* Code Based Data Objects Only - Utilize dictionaries, constants, etc to create roles and permissions
  * Pros: Allows for use of all Open edX defined i18n best practices
  * Cons: Does not allow for different roles on different systems, Slower data querying, 
* Database Only - Utilize database tables to store data and store translation data for the strings
  * Pros: Allows for different roles on different instances, Allows for easy addition of new roles
  * Cons: Requires custom built translation option 


The importance of i18n of the text displayed to users would support storing the data in the code. The importance of flexibility in creating new roles and between instances would support storing the data in a well structured set of database tables. Neither solution supports both requirements.

References
**********

`Writing Code for Internationalization ReadTheDocs <https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/internationalization/index.html>`_
