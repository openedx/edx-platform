Status: Active

Responsibilities
================
The user_api app is currently a catch all that is used to provide various apis that are related to the user and also to features within the platform.

Intended responsibility: To manage user profile and general account information and to provide APIs to do so easily. This includes the following features: user preference, user profile, user retirement, and account activation/deactivation.

Direction: Decompose
====================
Currently this app is a catch all for many user related information even when that information should really belong in a different app.  If you are building a feature and need to provide information about a user within the context of your feature, you should localize that API to your feature and make your assumptions about what user information you need clear.

For example authentication related APIs have already been moved to the user_authn django app.

Glossary
========

More Documentation
==================

Persisting Optional User Metadata
*********************************
The User API is capable of storing optional learner metadata through the use of a feature called the **Extended Profile**. The **Extended Profile** is a lightweight option for storing optional user data that doesn't require the modification or update of existing Django models.

This data is persisted as part of the ``meta`` field of a learner's UserProfile instance.

Storing data requires a *PATCH* request to be made to the User API endpoint.

This request data must include a key named **extended_profile** that contains a list of dictionaries representing the additional data we wish to store for the learners. Each dictionary in the list must include two fields:

* ``field_name``: A name describing the data to be stored
* ``field_value``: The data to be stored

An example request using *curl*, storing information in a field named ``occupation``:

.. code::
    curl --request PATCH '{{lms_host}}/api/user/v1/accounts/{{lms_username}}' \
    -- header 'Authorization: JWT {{jwt_token}}' \
    -- header 'Content-Type: application/merge-patch+json' \
    -- data '{
        "extended_profile": [
            {
                "field_name:" "occupation",
                "field_value": {
                    "name": "Organic Farmer",
                    "salary": "65000"
                }
            }
        ]
    }'

It is important to note that this data will not be returned as part of the User API until the system's Site Configuration has been updated. Details on how to update the Site Configuration can be found `here`_.

.. _here: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/retrieve_extended_profile_metadata.html
