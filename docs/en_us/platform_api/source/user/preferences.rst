.. _User Preferences API:

##################################################
User Preferences API
##################################################

This page contains information on using the User Preferences API to
complete the following actions.

* `Get and Update the User's Preferences Information`_
* `Get, Update, or Delete a Specific Preference`_

.. _Get and Update the User's Preferences Information:

**************************************************
Get and Update the User's Preferences Information
**************************************************

.. autoclass:: user_api.preferences.views.PreferencesView

**Example response showing the user's preference information**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS, PATCH

    {
      "pref-lang": "en", 
      "account_privacy": "private"    
    } 

.. _Get Update or Delete a Specific Preference:

**************************************************
Get, Update, or Delete a Specific Preference
**************************************************

.. autoclass:: user_api.preferences.views.PreferencesDetailView

**Example response to a request for the user's account_privacy setting**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS, PATCH

    "private"

