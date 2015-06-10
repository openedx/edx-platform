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

    config = {
        // NOTE: baseUrl has been previously set in lms/static/templates/main.html
        waitSeconds: 60,
        paths: {
            "annotator_1.2.9": "js/vendor/edxnotes/annotator-full.min",
            "date": "js/vendor/date",
            "text": 'js/vendor/requirejs/text',
            "backbone": "js/vendor/backbone-min",
            "backbone-super": "js/vendor/backbone-super",
            "backbone.paginator": "js/vendor/backbone.paginator.min",
            "underscore.string": "js/vendor/underscore.string.min",
            // Files needed by OVA
            "annotator": "js/vendor/ova/annotator-full",
            "annotator-harvardx": "js/vendor/ova/annotator-full-firebase-auth",
            "video.dev": "js/vendor/ova/video.dev",
            "vjs.youtube": 'js/vendor/ova/vjs.youtube',
            "rangeslider": 'js/vendor/ova/rangeslider',
            "share-annotator": 'js/vendor/ova/share-annotator',
            "richText-annotator": 'js/vendor/ova/richText-annotator',
            "reply-annotator": 'js/vendor/ova/reply-annotator',
            "grouping-annotator": 'js/vendor/ova/grouping-annotator',
            "tags-annotator": 'js/vendor/ova/tags-annotator',
            "diacritic-annotator": 'js/vendor/ova/diacritic-annotator',
            "flagging-annotator": 'js/vendor/ova/flagging-annotator',
            "jquery-Watch": 'js/vendor/ova/jquery-Watch',
            "openseadragon": 'js/vendor/ova/openseadragon',
            "osda": 'js/vendor/ova/OpenSeaDragonAnnotation',
            "ova": 'js/vendor/ova/ova',
            "catch": 'js/vendor/ova/catch/js/catch',
            "handlebars": 'js/vendor/ova/catch/js/handlebars-1.1.2'
            // end of files needed by OVA
        },
        shim: {
            "annotator_1.2.9": {
                deps: ["jquery"],
                exports: "Annotator"
            },
            "date": {
                exports: "Date"
            },
            "jquery": {
                exports: "$"
            },
            "underscore": {
                exports: "_"
            },
            "backbone": {
                deps: ["underscore", "jquery"],
                exports: "Backbone"
            },
            "backbone.paginator": {
                deps: ["backbone"],
                exports: "Backbone.Paginator"
            },
            "backbone-super": {
                deps: ["backbone"]
            },
            "logger": {
                exports: "Logger"
            },
            // Needed by OVA
            "video.dev": {
                exports:"videojs"
            },
            "vjs.youtube": {
                deps: ["video.dev"]
            },
            "rangeslider": {
                deps: ["video.dev"]
            },
            "annotator": {
                exports: "Annotator"
            },
            "annotator-harvardx":{
                deps: ["annotator"]
            },
            "share-annotator": {
                deps: ["annotator"]
            },
            "richText-annotator": {
                deps: ["annotator", "tinymce"]
            },
            "reply-annotator": {
                deps: ["annotator"]
            },
            "tags-annotator": {
                deps: ["annotator"]
            },
            "diacritic-annotator": {
              deps: ["annotator"]
            },
            "flagging-annotator": {
                deps: ["annotator"]
            },
            "grouping-annotator": {
                deps: ["annotator"]
            },
            "ova": {
                exports: "ova",
                deps: [
                    "annotator", "annotator-harvardx", "video.dev", "vjs.youtube", "rangeslider", "share-annotator",
                    "richText-annotator", "reply-annotator", "tags-annotator", "flagging-annotator",
                    "grouping-annotator", "diacritic-annotator", "jquery-Watch", "catch", "handlebars", "URI"
                ]
            },
            "osda": {
                exports: "osda",
                deps: [
                    "annotator", "annotator-harvardx", "video.dev", "vjs.youtube", "rangeslider", "share-annotator",
                    "richText-annotator", "reply-annotator", "tags-annotator", "flagging-annotator",
                    "grouping-annotator", "diacritic-annotator", "openseadragon", "jquery-Watch", "catch", "handlebars",
                    "URI"
                ]
            }
            // End of needed by OVA
        }
    };

    for (var key in paths) {
        if ({}.hasOwnProperty.call(paths, key)) {
            config.paths[key] = paths[key];
        }
    }
    require.config(config);
}).call(this, require || RequireJS.require, define || RequireJS.define);
