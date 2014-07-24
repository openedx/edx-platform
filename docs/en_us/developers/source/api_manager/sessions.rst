###############################
Sessions API Module
###############################

.. module:: api_manager

The page contains docstrings and example responses for:

* `Create a Session`_
* `Get Session Details`_
* `Delete a Session`_

.. _Create a Session:

**************************
Create a Session
**************************

.. autoclass:: sessions.views.SessionsList
    :members:

**Example post**

.. code-block:: json

    {
         "username": "name",
         "password": "password"
    }

**Example response**

.. code-block:: json

    HTTP 201 CREATED
    Vary: Accept
    Content-Type: text/html; charset=utf-8
    Allow: POST, OPTIONS

    {
        "token": "938680977d04ed091b67b974b6b6be60", 
        "expires": 604800, 
        "user": {
            "id": 4, 
            "email": "staff@example.com", 
            "username": "staff", 
            "first_name": "", 
            "last_name": "", 
            "created": "2014-04-18T13:44:25Z", 
            "organizations": []
        }, 
        "uri": "http://localhost:8000/api/sessions?username=staff&password=edx/938680977d04ed091b67b974b6b6be60"
    }


.. _Get Session Details:

**************************
Get Session Details
**************************

.. autoclass:: sessions.views.SessionsDetail
    :members:

**Example GET response**

.. code-block:: json

    HTTP 200 OK
    Vary: Accept
    Content-Type: text/html; charset=utf-8
    Allow: GET, DELETE, HEAD, OPTIONS

    {
        "token": "8c510db85585c64bd33bede01d645a60", 
        "expires": 1209600, 
        "user_id": 1, 
        "uri": "http://localhost:8000/api/sessions//8c510db85585c64bd33bede01d645a60"
    }

.. _Delete a Session:

**************************
Delete a Session
**************************

.. autoclass:: sessions.views.SessionsDetail
    :members:

**Example DELETE response**

.. code-block:: json

    HTTP 204 NO CONTENT
    Vary: Accept
    Content-Type: text/html; charset=utf-8
    Allow: GET, DELETE, HEAD, OPTIONS

    {}