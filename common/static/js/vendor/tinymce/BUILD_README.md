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
4. Move the tinymce-codemirror/plugins directory to `common/static/js/vendor/tinymce/js/plugins/` directory.
5. Apply EDX specific changes in the existing code to the `plugin.js` and `source.html` files.
6. Install [uglify-js](https://www.npmjs.com/package/uglify-js) and generate `plugin.min.js`
    ```
    cd common/static/js/vendor/tinymce/js/plugins/codemirror/
    uglify plugin.js -m -o plugin.min.js
    ```
**IMPORTANT NOTE:** Regenerate the `tinymce.full.min.js` bundle everytime the code-mirror `plugin.min.js` is regenerated to ensure the latest changes are added to the bundle.

# Instructions for creating js/tinymce.full.min.js

The following uses the version 5.5.1 as a reference. Change your filenames depending the version you have downloaded.

1. Unzip the zip file downloaded from Github.
    ```
    unzip tinymce-5.5.1.zip
    ```
2. Open terminal and change directory to the newly downloaded tinymce.
    ```
    cd tinymce-5.5.1
    ```
3. Build TinyMCE using Yarn. this will create multiple zip files in the `dist` directory.
    ```
    yarn && yarn build
    ```
4. Unzip the dev bundle to the edx-platform's vendor directory.
    ```
    unzip dist/tinymce_5.5.1_dev.zip -d /path/to/edx-platform/common/static/js/vendor/
    ```
5. Remove the unnecessary files in `/path/to/edx-platform/common/static/js/vendor/tinymce` like `package.json`, `yarn.lock`...etc.,
6. Generate a bundled version of the TinyMCE with all the plugins using the following command
    ```
    cd common/static/js/vendor/tinymce/js/tinymce
    LC_ALL=C cat tinymce.min.js */*/*.min.js plugins/emoticons/js/emojis.min.js > tinymce.full.min.js
    ```
