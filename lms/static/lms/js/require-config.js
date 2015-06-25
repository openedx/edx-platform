;(function (require) {


require.config({
    // NOTE: baseUrl has been previously set in lms/templates/main.html
    waitSeconds: 60,
    paths: {
        "domReady": "js/vendor/domReady",
        "gettext": "/i18n",
        "annotator_1.2.9": "js/vendor/edxnotes/annotator-full.min",
        "date": "js/vendor/date",
        "text": 'js/vendor/requirejs/text',
        "logger": "js/src/logger",
        "backbone": "js/vendor/backbone-min",
        "backbone-super": "js/vendor/backbone-super",
        "underscore": "js/vendor/underscore-min",
        "underscore.string": "js/vendor/underscore.string.min",
        "jquery.cookie": "js/vendor/jquery.cookie",
        "jquery.tinymce": "js/vendor/tinymce/js/tinymce/jquery.tinymce.min",
        "jquery.url": "js/vendor/url.min",
        "jquery-Watch": "js/vendor/ova/jquery-Watch",
        "URI": "js/vendor/URI.min",
        "string_utils": "js/src/string_utils",

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
        "jquery": "js/vendor/jquery.min",
        "openseadragon": 'js/vendor/ova/openseadragon',
        "osda": 'js/vendor/ova/OpenSeaDragonAnnotation',
        "ova": 'js/vendor/ova/ova',
        "catch": 'js/vendor/ova/catch/js/catch',
        "handlebars": 'js/vendor/ova/catch/js/handlebars-1.1.2'
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
        "jquery.url": {
            deps: ["jquery"],
            exports: "jQuery.url"
        },
        "underscore": {
            exports: "_"
        },
        "backbone": {
            deps: ["underscore", "jquery"],
            exports: "Backbone"
        },
        "backbone-super": {
            deps: ["backbone"]
        },
        "logger": {
            exports: "Logger",
            deps: ["coffee/src/ajax_prefix"]
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
        }
        // End of needed by OVA
    }
});
}).call(this, require || RequireJS.require);
