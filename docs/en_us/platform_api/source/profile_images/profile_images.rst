.. Profile Images API:

##################################################
Profile Images API Profile Images Resource
##################################################

With the Profile Images API **Profile Images** resource, you can complete the
following tasks.

* :ref:`Upload a profile image <Upload a Profile Image>`.
* :ref:`Remove profile images <Remove a Profile Image>`.

.. _Upload a Profile Image:

**************************************************
Upload a Profile Image
**************************************************

.. autoclass:: profile_images.views.ProfileImageUploadView

**Example Response**

.. code-block:: json

    HTTP 204
    No Content


.. _Remove a Profile Image:

**************************************************
Remove a Profile Image
**************************************************

.. autoclass:: profile_images.views.ProfileImageRemoveView

**Example Response**

.. code-block:: json

    HTTP 204
    No Content
