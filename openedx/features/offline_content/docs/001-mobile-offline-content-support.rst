===================================================
Offline Mode content generation for mobile OeX app
===================================================

Status
------

Proposed

Context and Problem Statement
-----------------------------

The primary goal is to enable offline access to course content in the Open edX mobile application.
This will allow users to download course materials when they have internet access and access them
later without an internet connection. This feature is crucial for learners in areas with unreliable
internet connectivity or those who prefer to study on the go without using mobile data.

Decision Drivers
----------------

* **User Convenience**: Improve the learning experience by allowing access to course materials anytime, anywhere.
* **Accessibility**: Ensure learners in regions with limited or no internet connectivity can still benefit from the educational content.
* **Platform Compatibility**: Maintain compatibility with existing Open edX infrastructure and mobile applications.
* **Performance**: Ensure that the offline mode does not degrade the performance of the mobile application.

Considered Options
------------------

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
