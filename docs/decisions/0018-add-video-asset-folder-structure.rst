Add new ability to store course assets and videos in folders
============================================================

Status
------
Proposed


Context
-------

We are planning to add folders to the Studio assets and video pages. The number
of folders can be infinite and have infinite depth. The folders will be visible
on the "Files & Media" page in the course-authoring MFE and in modals that allow
users to select files to insert into their course content, i.e. editors, custom
pages, etc.

Assets are stored in contentstore, a GridFS/MongoDB database that already supports
folders. There are courses on edx.org that utilize this capability and the folders
can be seen during import/export. The folder/file path is stored in the import_path
field. We will just need to add a parser to break down the import_path string and
check that duplicate folders are not created. This path will have to be updated
each time a file is moved in and out of folders. The main work that needs to be
done is a user interface that allows users to create, delete, and/or update folders.

Videos are stored in AWS S3 buckets. Similar to GridFS/MongoDB, AWS allows a file's
key to have a prefix. The prefix is a path that acts like a folder to distinguish
the location of different files. The prefix requires a unique delimiter, like a
forward slash (/). This is an example of what some keys might look like:

  sample.jpg
  photos/2006/January/sample.jpg
  photos/2006/February/sample2.jpg
  photos/2006/February/sample3.jpg
  photos/2006/February/sample4.jpg

It is important to note that prefixes do not render physical folder/subfolder
relationships like you expect from a file system manager. All the videos will live
at the same heirachal level, but the prefixes will separate them and allow for queries
dependent on the path. This will keep the existing video references backwards
compatible. For further reading check the `Organizing objects using prefixes article
<https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html>`_ from AWS.
