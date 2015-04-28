################################################
User API Endpoints
################################################

You use the User API to view information about users and update
your own account.

The following tasks and endpoints are currently supported. 

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - To:
     - Use this endpoint:
   * - :ref:`Get a user's account information <Get and Update the User's
       Account Information>`
     - GET /api/user/v1/accounts/{username}/[?view=shared]
   * - :ref:`Update your account information <Get and Update the User's Account
       Information>`
     - PATCH /api/user/v1/accounts/{username}/{“key”:”value”}
   * - :ref:`Get a user's preferences information <Get and Update the User's
       Preferences Information>`
     - GET /api/user/v1/preferences/{username}/
   * - :ref:`Update a user's preferences information <Get and Update the User's
       Preferences Information>`
     - PATCH /api/user/v1/preferences/{username}/
   * - :ref:`Get a specific preference <Get Update or Delete a Specific
       Preference>`
     - GET /api/user/v1/preferences/{username}/{preference_key}
   * - :ref:`Update a specific preference <Get Update or Delete a Specific
       Preference>`
     - PUT /api/user/v1/preferences/{username}/{preference_key}
   * - :ref:`Delete a specific preference <Get Update or Delete a Specific
       Preference>`
     - DELETE /api/user/v1/preferences/{username}/{preference_key}
