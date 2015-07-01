;(function (require, define) {
    var paths = {}, config;

    // jquery, underscore, gettext, URI, tinymce, or jquery.tinymce may already
    // have been loaded and we do not want to load them a second time. Check if
    // it is the case and use the global var instead.
    if (window.jQuery) {
        define("jquery", [], function() {return window.jQuery;});
    } else {
        paths.jquery = "js/vendor/jquery.min";
    }
    if (window._) {
        define("underscore", [], function() {return window._;});
    } else {
        paths.jquery = "js/vendor/underscore-min";
    }
    if (window.gettext) {
        define("gettext", [], function() {return window.gettext;});
    } else {
        paths.gettext = "/i18n";
    }
    if (window.Logger) {
        define("logger", [], function() {return window.Logger;});
    } else {
        paths.logger = "js/src/logger";
    }
    if (window.URI) {
        define("URI", [], function() {return window.URI;});
    } else {
        paths.URI = "js/vendor/URI.min";
    }
    if (window.tinymce) {
        define('tinymce', [], function() {return window.tinymce;});
    } else {
        paths.tinymce = "js/vendor/tinymce/js/tinymce/tinymce.full.min";
    }
    if (window.jquery && window.jquery.tinymce) {
        define("jquery.tinymce", [], function() {return window.jquery.tinymce;});
    } else {
        paths.tinymce = "js/vendor/tinymce/js/tinymce/jquery.tinymce.min";
    }
    require.config(config);
}).call(this, require || RequireJS.require, define || RequireJS.define);
