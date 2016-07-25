;(function (require, define) {

    // We do not wish to bundle common libraries (that may also be used by non-RequireJS code on the page
    // into the optimized files. Therefore load these libraries through script tags and explicitly define them.
    // Note that when the optimizer executes this code, window will not be defined.
    if (window) {
        var defineDependency = function (globalVariable, name, noShim) {
            if (window[globalVariable]) {
                if (noShim) {
                    define(name, {});
                }
                else {
                    define(name, [], function() {return window[globalVariable];});
                }
            }
            else {
                console.error("Expected library to be included on page, but not found on window object: " + name);
            }
        };

        defineDependency("jQuery", "jquery");

        /*
        defineDependency("_", "underscore");
        defineDependency("gettext", "gettext");
        defineDependency("Logger", "logger");
        defineDependency("URI", "URI");
        defineDependency("Backbone", "backbone");


        // utility.js adds two functions to the window object, but does not return anything
        defineDependency("isExternal", "utility", true);
        */
    }

    require.config({
        // NOTE: baseUrl has been previously set in lms/templates/main.html
        waitSeconds: 60,
        paths: {
            "gettext": "/i18n",
            "annotator_1.2.9": "js/vendor/edxnotes/annotator-full.min",
            "date": "js/vendor/date",
            "moment": "js/vendor/moment.min",
            "moment-with-locales": "xmodule_js/common_static/js/vendor/moment-with-locales.min",
            "text": "js/vendor/requirejs/text",
            "logger": "js/src/logger",
            "backbone": "js/vendor/backbone-min",
            "backbone-super": "js/vendor/backbone-super",
            "backbone.paginator": "js/vendor/backbone.paginator.min",
            "underscore": "js/vendor/underscore-min",
            "underscore.string": "js/vendor/underscore.string.min",
            "jquery": "js/vendor/jquery.min",
            "jquery.cookie": "js/vendor/jquery.cookie",
            'jquery.timeago': 'js/vendor/jquery.timeago',
            "jquery.url": "js/vendor/url.min",
            "jquery.ui": "js/vendor/jquery-ui.min",
            "jquery.iframe-transport": "js/vendor/jQuery-File-Upload/js/jquery.iframe-transport",
            "jquery.fileupload": "js/vendor/jQuery-File-Upload/js/jquery.fileupload",
            "URI": "js/vendor/URI.min",
            "string_utils": "js/src/string_utils",
            "utility": "js/src/utility",

            // Files needed by OVA
            "annotator": "js/vendor/ova/annotator-full",
            "annotator-harvardx": "js/vendor/ova/annotator-full-firebase-auth",
            "video.dev": "js/vendor/ova/video.dev",
            "vjs.youtube": "js/vendor/ova/vjs.youtube",
            "rangeslider": "js/vendor/ova/rangeslider",
            "share-annotator": "js/vendor/ova/share-annotator",
            "richText-annotator": "js/vendor/ova/richText-annotator",
            "reply-annotator": "js/vendor/ova/reply-annotator",
            "grouping-annotator": "js/vendor/ova/grouping-annotator",
            "tags-annotator": "js/vendor/ova/tags-annotator",
            "diacritic-annotator": "js/vendor/ova/diacritic-annotator",
            "flagging-annotator": "js/vendor/ova/flagging-annotator",
            "jquery-Watch": "js/vendor/ova/jquery-Watch",
            "openseadragon": "js/vendor/ova/openseadragon",
            "osda": "js/vendor/ova/OpenSeaDragonAnnotation",
            "ova": "js/vendor/ova/ova",
            "catch": "js/vendor/ova/catch/js/catch",
            "handlebars": "js/vendor/ova/catch/js/handlebars-1.1.2",
            "tinymce": "js/vendor/tinymce/js/tinymce/tinymce.full.min",
            "jquery.tinymce": "js/vendor/tinymce/js/tinymce/jquery.tinymce.min"
            // end of files needed by OVA
        },
        shim: {
            "gettext": {
                exports: "gettext"
            },
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
            "jquery.cookie": {
                deps: ["jquery"],
                exports: "jQuery.fn.cookie"
            },
            "jquery.timeago": {
                deps: ["jquery"],
                exports: "jQuery.timeago"
            },
            "jquery.url": {
                deps: ["jquery"],
                exports: "jQuery.url"
            },
            "jquery.fileupload": {
                deps: ["jquery.ui", "jquery.iframe-transport"],
                exports: "jQuery.fn.fileupload"
            },
            "jquery.tinymce": {
                deps: ["jquery", "tinymce"],
                exports: "jQuery.fn.tinymce"
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
            "string_utils": {
                deps: ["underscore"],
                exports: "interpolate_text"
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
            },
            "tinymce": {
                exports: "tinymce"
            },
            // End of needed by OVA
            "moment": {
                exports: "moment"
            },
            "moment-with-locales": {
                exports: "moment"
            }
        }
    });
}).call(this, require || RequireJS.require, define || RequireJS.define);
