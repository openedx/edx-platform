################################################
Profile Images API Endpoints
################################################

You use the Profile Images API to upload or remove profile images.

If you have staff access, you can remove profile images from any user
account.

The following tasks and endpoints are currently supported. 

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - To:
     - Use this endpoint:
   * - :ref:`Upload a profile image <Upload a Profile Image>`
     - POST /api/profile_images/v1/{username}/upload
   * - :ref:`Remove profile images <Remove Profile Images>`
     - POST /api/profile_images/v1/{username}/remove
