Offline content generation for mobile OeX app
=============================================

Status
------

Proposed

Context
-------

The primary goal is to enable offline access to course content in the Open edX mobile application.
This will allow users to download course materials when they have internet access and access them
later without an internet connection, also it should support synchronization of the submitted results
with backend service as connection become available again. This feature is crucial for learners
in areas with unreliable internet connectivity or those who prefer to study on the go without using mobile data.
It is possible to provide different kind of content using the Open edX platform, such as read-only materials,
videos, and assessments. Therefore to provide the whole course experience in offline mode it's required to 
make all these types of content available offline. Of course it won't be feasible to recreate grading
algorithms in mobile, so it's possible to save submission on the mobile app and execute synchronization 
of the user progres as not limited conectivity is back.
From the product perspective the following Figma designs and product requirements should be considered:
* Figma
* Offline mode product pages


Decision
--------

The implementation of the offline content support require addition of the following features to the edx-platform:

* It's necessary to generate an archive with all necessary HTML and assets for a student view of an xBlock,
   so it's possible to display an xBlock using mobile WebView.
* The generated offline content should be provided to mobile device through mobile API.
* To support CAPA problems and other kinds of assessments in offline mode it's necessary to create an additional
  JavaScript layer that will allow communication with Mobile applications by sending JSON messages
  using Android and IOS Bridge.
  
  
  
Offline content generation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Generating zip archive with xBlock data for HTML and CAPA problems
When content is published in CMS and offline generation is enabled for the course or entire platform using waffle flags, the content generation task should be started for supported blocks.
Every time block content republished ZIP archive with offline content should be regenerated.
The xBlock should be rendered the same way it’s rendered for a student using /xblock/{locator.id} endpoint in LMS.
HTML should be processed, all related assets files, images and scripts should be included in the generated ZIP archive with offline content
The Generation process should work with local media storage as well as s3.
If error retrieving block happened, the generation task will be scheduled for retry 2 more times, with progressive delay.

Mobile API extension
~~~~~~~~~~~~~~~~~~~~

Extend mobile API endpoint for Course Home, to return information about offline content available for download for supported blocks
{
...
"offline_download": {
    "file_url": "{file_url}" or null,
    "last_modified": "{DT}" or null,
    "file_size": ""
  }
}

JavaScript Bridge for interaction with mobile applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Implement JS Bridge JS script to intercept and send results to mobile device for supported CAPA problems
The submission data should be sent via bridge to IOS and Android devices.
This script should expose markCompleted JS function so mobile can change state of the offline problem after the data was saved into internal database or on initialization of the problem


* **Implement of a mechanism for generating and storing on a server or external storage**: The course content should be pre-generated and saved to the storage for later download.
    * **Render content**: Generate HTML content of block as it does for LMS.
    * **Replace static and media**: Save static and media assets files used in block to temporary directory and replace their static paths with local paths.
    * **Archive and store content**: Archive the generated content and store it on the server or external storage.
* **Mechanism for updating the generated data**: When updating course blocks (namely when publishing) the content that has been changed should be re-generated.
    * **Track course publishing events on CMS side**: Signal in the CMS that makes request to LMS to update course content.
    * **Track course publishing events on LMS side**: API endpoint to receive the signal from CMS and update course content.
    * **Update archive**: Check generated archive creation date and update it if less than course publishing date.
* **Implement a Mobile Local Storage Mechanism**: Use the device's local storage to save course content for offline access.
    * **Extend blocks API**: Add links to download blocks content and  where it is possible.
* **Sync Mechanism**: Periodically synchronize local data with the server when the device is online.
    * **Sync on app side**: On course outline screen, check if the course content is up to date and update it if necessary.
* **Selective Download**: Allow users to choose specific content to download for offline use.
* **Full Course Download**: Provide an option to download entire courses for offline access.

Supported xBlocks in offline mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It was decided to include a fraction of Open edX xBlocks to be supported 


Consequences
------------

* Enhanced learner experience with flexible access to course materials.
* Increased accessibility for learners in regions with poor internet connectivity.
* Improved engagement and completion rates due to uninterrupted access to content.
* Potential increase in app size due to locally stored content.
* Increased complexity in managing content synchronization and updates.
* Need for continuous monitoring and updates to handle new content types and formats.

Rejected Solutions
------------------

Store common .js and .css files of blocks in a separate folder:
    * This solution was rejected because it is unclear how to track potential changes to these files and re-generate the content of the blocks.

Generate content on the fly when the user requests it:
    * This solution was rejected because it would require a significant amount of processing power and time to generate content for each block when requested.
