Instructions for creating js/tinymce.full.min.js

1. Unzip vendor_extra/tinymce/jake_package.zip into this directory (so that Jakefile.js resides in this directory).
2. Run the following command:
   jake minify bundle[themes:modern,plugins:image,link,codemirror,paste,table,textcolor]
3. Cleanup by deleting the Unversioned files that were created from unzipping jake_package.zip.

Instructions for updating tinymce to a newer version:

1. Download the desired version from https://github.com/tinymce/tinymce/releases
2. Find all the EDX specific changes that were made to the currently used version of tinymce by searching for
   the string "EDX" in this directory.
3. Merge the EDX specific changes with the new version.
4. Follow the instructions above for creating the new version of js/tinymce.full.min.js
