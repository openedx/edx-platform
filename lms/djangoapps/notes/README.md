Notes Django App
=================

This is a django application that stores and displays notes that students make while reading static HTML book(s) in their courseware.  Note taking functionality in the static HTML book(s) is handled by a wrapper script around [annotator.js](http://okfnlabs.org/annotator/), which interfaces with the API provided by this application to store and retrieve notes.

Usage
-----

To use this application, course staff must *opt-in* by doing the following:

# Login to (http://studio.edx.org/)[Studio].
# Go to *Course Settings* -> *Advanced Settings*
# Find the ```advanced_modules``` policy key and in the policy value field, add ```"notes"``` to the list. 
# Save the course settings.

The result of following these steps is that you should see a new tab appear in the courseware named *My Notes*. This will display a journal of notes that the student has created in the static HTML book(s). Second, when you highlight text in the static HTML book(s), a dialog will appear. You can enter some notes and tags and save it. The note will appear highlighted in the text and will also be saved to the journal. 

To disable the *My Notes* tab and notes in the static HTML book(s), simply reverse the above steps (i.e. remove ```"notes"``` from the ```advanced_modules``` policy setting).

### Caveats and Limitations

* Notes are private to each student. 
* Sharing and replying to notes is not supported.
* The student *My Notes* interface is very limited. 
* There is no instructor interface to view student notes.
