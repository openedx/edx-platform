/**
 * the Programs application loads gettext identity library via django, thus
 * components reference gettext globally so a shim is added here to reflect
 * the text so tests can be run if modules reference gettext
 */
(function() {
    'use strict';

    if ( !window.gettext ) {
        window.gettext = function (text) {
            return text;
        };
    }

    if ( !window.interpolate ) {
        window.interpolate = function (text) {
            return text;
        };
    }

    return window;
})();
