========================
Import from Modulestore
========================

The new Django application `import_from_modulestore` is designed to
automate the process of importing course legacy OLX content from Modulestore
to Content Libraries. The application allows users to easily and quickly
migrate existing course content, minimizing the manual work and potential
errors associated with manual migration.
The new app makes the import process automated and easy to manage.

The main problems solved by the application:

* Reducing the time to import course content.
* Ensuring data integrity during the transfer.
* Ability to choose which content to import before the final import.

------------------------------
Import from Modulestore Usage
------------------------------

* Import course elements at the level of sections, subsections, units,
  and xblocks into the Content Libraries.
* Choose the structure of this import, whether it will be only xblocks
  from a particular course or full sections/subsections/units.
* Store the history of imports.
* Synchronize the course content with the library content (when re-importing,
  the blocks can be updated according to changes in the original course).
* The new import mechanism ensures data integrity at the time of importing
  by saving the course in StagedContent.
* Importing the legacy library content into the new Content Libraries.
