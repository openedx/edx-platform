;(function (require, define) {
    'use strict';
    var config = {};
    config.paths = {};

    // jquery, underscore, gettext, URI, tinymce, or jquery.tinymce may already
    // have been loaded and we do not want to load them a second time. Check if
    // it is the case and use the global var instead.
    if (window.jQuery) {
        define("jquery", [], function() {return window.jQuery;});
    }

    if (window._) {
        define("underscore", [], function() {return window._;});
    }

    if (window.gettext) {
        define("gettext", [], function() {return window.gettext;});
    }

    if (window.Logger) {
        define("logger", [], function() {return window.Logger;});
    }

    if (window.URI) {
        define("URI", [], function() {return window.URI;});
    }

    if (window.tinymce) {
        define('tinymce', [], function() {return window.tinymce;});
    }

    if (window.jquery && window.jquery.tinymce) {
        define("jquery.tinymce", [], function() {return window.jquery.tinymce;});
    }
    require.config(config);
}).call(this, require || RequireJS.require, define || RequireJS.define);
