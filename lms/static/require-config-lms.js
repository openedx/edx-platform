;(function (require, define, _) {
    var paths = {}, config;

    // URI, tinymce, or jquery.tinymce may already have been loaded before the OVA templates and we do not want to load
    // them a second time. Check if it is the case and use the global var in requireJS config.
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
        // NOTE: baseUrl has been previously set in lms/templates/main.html
        waitSeconds: 60,
        paths: {
            // Files only needed for OVA
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
            "handlebars": 'js/vendor/ova/catch/js/handlebars-1.1.2',
            // end of files only needed for OVA
        },
        shim: {
            // The following are all needed for OVA
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
            // End of OVA
        }
    };
    _.extend(config.paths, paths);
    require.config(config);
}).call(this, require || RequireJS.require, define || RequireJS.define, _);
