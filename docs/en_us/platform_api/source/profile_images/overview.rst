################################################
Profile Images Overview
################################################

Use the Profile Images API to upload or remove profile images.

The requesting user can upload or remove his or her own profile image.

Users with staff access can remove profile images from any user account.

.. contents::
   :local:
   :depth: 1

*************************************
Profile Images API Version and Status
*************************************

The Profile Images API is currently at version 1.0.

**********************************************
Profile Images API Endpoints
**********************************************

The Profile Images API supports the following tasks, methods, and endpoints.

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Upload a profile image <Upload a Profile Image>`
     - POST 
     - /api/profile_images/v1/{username}/upload
   * - :ref:`Remove a profile image <Remove a Profile Image>`
     - POST 
     - /api/profile_images/v1/{username}/remove