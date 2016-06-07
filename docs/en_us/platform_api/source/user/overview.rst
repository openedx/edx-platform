################################################
User API Overview
################################################

Use the User API to view and update account and preference information.

.. contents::
   :local:
   :depth: 1

*************************************
User API Version and Status
*************************************

The User API is currently at version 1.0. We plan on making
significant enhancements to this API.

**********************************************
User API Resources and Endpoints
**********************************************

The User API supports the following resources, tasks, methods, and endpoints.

=============================
User Accounts API Resource
=============================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get a user's account information <Get and Update the User's
       Account Information>`
     - GET 
     - /api/user/v1/accounts/{username}/[?view=shared]
   * - :ref:`Update your account information <Get and Update the User's Account
       Information>`
     - PATCH 
     - /api/user/v1/accounts/{username}/{“key”:”value”}


=============================
User Preferences API Resource
=============================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get a user's preferences information 
       <Get and Update the User's Preferences Information>`
     - GET
     - /api/user/v1/preferences/{username}/
   * - :ref:`Update a user's preferences information 
       <Get and Update the User's Preferences Information>`
     - PATCH
     - /api/user/v1/preferences/{username}/
   * - :ref:`Get a specific preference 
       <Get Update or Delete a Specific Preference>`
     - GET
     - /api/user/v1/preferences/{username}/{preference_key}
   * - :ref:`Update a specific preference 
       <Get Update or Delete a Specific Preference>`
     - PUT
     - /api/user/v1/preferences/{username}/{preference_key}
   * - :ref:`Delete a specific preference 
       <Get Update or Delete a Specific Preference>`
     - DELETE
     - /api/user/v1/preferences/{username}/{preference_key}
