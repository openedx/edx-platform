/**
 * Client-side logic to support XBlock authoring.
 */
var edx = edx || {};

(function($) {
    'use strict';

    edx.studio = edx.studio || {};
    edx.studio.xblock = edx.studio.xblock || {};

    function initializeVisibilityEditor(runtime, element) {
        element.find('.field-visibility-level input').change(function(event) {
            if ($(event.target).hasClass('visibility-level-all')) {
                element.find('.field-visibility-content-group input').prop('checked', false);
            }
        });
        element.find('.field-visibility-content-group input').change(function(event) {
            element.find('.visibility-level-all').prop('checked', true);
            element.find('.visibility-level-specific').prop('checked', true);
        });
    }

    // XBlock initialization functions must be global
    window.VisibilityEditorInit = initializeVisibilityEditor;
})($);
