/**
 * Client-side logic to support XBlock authoring.
 */
var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.studio = edx.studio || {};
    edx.studio.xblock = edx.studio.xblock || {};

    function initializeVisibilityEditor(runtime, element) {
        // TODO: let's do something here!
    }

    // XBlock initialization functions must be global
    window.VisibilityEditorInit = initializeVisibilityEditor;
})($, _, gettext);
