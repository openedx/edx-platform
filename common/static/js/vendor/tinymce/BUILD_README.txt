# Instructions for updating tinymce to a newer version:

1. Download the desired version from https://github.com/tinymce/tinymce/tags
2. If it’s a major update, follow the official migration doc and update the codebase as needed.
3. Setup the codemirror-plugin as per the instruction below.
4. Find all the EDX specific changes in the currently used version of tinymce by searching for the string "EDX" in the vendor/js/tinymce dir.
5. Merge the EDX specific changes with the newly downloaded version.
6. Follow the instructions given below to create the new version of js/tinymce.full.min.js

# Instruction for setting codemirror-plugin

1. Download the tinymce-codemirror-plugin from https://gitlab.com/tinymce-plugins/tinymce-codemirror
2. Open terminal in the downloaded plugin directory and run the following commands:
  ```
   npm install
   npm run prepublish (This command will generate the minified file in the plugin directory)
  ```
3. Remove the tinymce-codemirror/plugins/codemirror/codemirror-4.8 directory
4. Move the tinymce-codemirror/plugins directory to common/static/js/vendor/tinymce/js/plugins/ directory.

# Instructions for creating js/tinymce.full.min.js

1. Follow the README file of the downloaded tinymce’s codebase and install all the requirements.
2. Open terminal and change directory to the newly downloaded tinymce.
3. Run the build command: “yarn build”, this will create multiple zip files in the build directory.
4. Unzip the tinymce_<version>.zip file in common/static/vendor/js/
5. Unzip vendor_extra/tinymce/JakePackage.zip in  common/static/vendor/js/tinymce/.
6. Run the following command in the tinymce directory: npx jake minify bundle[themes:silver,plugins:*]
7. Cleanup by deleting the unversioned files that were created from unzipping jake_package.zip.
