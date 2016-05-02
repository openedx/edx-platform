;(function (require, define) {
    'use strict';
    if (window) {
        // MathJax Fast Preview was introduced in 2.5. However, it
        // causes undesirable flashing/font size changes when
        // MathJax is used for interactive preview (equation editor).
        // Setting processSectionDelay to 0 (see below) fully eliminates
        // fast preview, but to reduce confusion, we are also setting
        // the option as displayed in the context menu to false.
        // When upgrading to 2.6, check if this variable name changed.
        window.MathJax = {
            menuSettings: {CHTMLpreview: false}
        };
        // Since we are serving the gettext catalog as static files,
        // the URL for the gettext file will vary depending on which locale
        // needs to be served. To handle this, we load the correct file in the
        // rendered template and then use this to ensure that RequireJS knows
        // how to find it.
        define("gettext", function () { return window.gettext; });
    }

    require.config({
        // NOTE: baseUrl has been previously set in cms/static/templates/base.html
        waitSeconds: 60,
        paths: {
            "domReady": "js/vendor/domReady",
            "mustache": "js/vendor/mustache",
            "codemirror": "js/vendor/codemirror-compressed",
            "codemirror/stex": "js/vendor/CodeMirror/stex",
            "jquery": "common/js/vendor/jquery",
            "jquery-migrate": "common/js/vendor/jquery-migrate",
            "jquery.ui": "js/vendor/jquery-ui.min",
            "jquery.form": "js/vendor/jquery.form",
            "jquery.markitup": "js/vendor/markitup/jquery.markitup",
            "jquery.leanModal": "js/vendor/jquery.leanModal",
            "jquery.ajaxQueue": "js/vendor/jquery.ajaxQueue",
            "jquery.smoothScroll": "js/vendor/jquery.smooth-scroll.min",
            "jquery.timepicker": "js/vendor/timepicker/jquery.timepicker",
            "jquery.cookie": "js/vendor/jquery.cookie",
            "jquery.qtip": "js/vendor/jquery.qtip.min",
            "jquery.scrollTo": "js/vendor/jquery.scrollTo.min",
            "jquery.flot": "js/vendor/flot/jquery.flot.min",
            "jquery.fileupload": "js/vendor/jQuery-File-Upload/js/jquery.fileupload",
            "jquery.fileupload-process": "js/vendor/jQuery-File-Upload/js/jquery.fileupload-process",
            "jquery.fileupload-validate": "js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate",
            "jquery.iframe-transport": "js/vendor/jQuery-File-Upload/js/jquery.iframe-transport",
            "jquery.inputnumber": "js/vendor/html5-input-polyfills/number-polyfill",
            "jquery.immediateDescendents": "coffee/src/jquery.immediateDescendents",
            "datepair": "js/vendor/timepicker/datepair",
            "date": "js/vendor/date",
            "moment": "js/vendor/moment.min",
            "moment-with-locales": "js/vendor/moment-with-locales.min",
            "text": 'js/vendor/requirejs/text',
            "underscore": "common/js/vendor/underscore",
            "underscore.string": "common/js/vendor/underscore.string",
            "backbone": "common/js/vendor/backbone",
            "backbone-relational" : "js/vendor/backbone-relational.min",
            "backbone.associations": "js/vendor/backbone-associations-min",
            "backbone.paginator": "js/vendor/backbone.paginator.min",
            "tinymce": "js/vendor/tinymce/js/tinymce/tinymce.full.min",
            "jquery.tinymce": "js/vendor/tinymce/js/tinymce/jquery.tinymce.min",
            "xmodule": "/xmodule/xmodule",
            "xblock/core": "js/xblock/core",
            "xblock": "coffee/src/xblock",
            "utility": "js/src/utility",
            "accessibility": "js/src/accessibility_tools",
            "URI": "js/vendor/URI.min",
            "ieshim": "js/src/ie_shim",
            "tooltip_manager": "js/src/tooltip_manager",
            "modernizr": "edx-pattern-library/js/modernizr-custom",
            "afontgarde": "edx-pattern-library/js/afontgarde",
            "edxicons": "edx-pattern-library/js/edx-icons",
            "draggabilly": "js/vendor/draggabilly",

            // Files needed for Annotations feature
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
            "lang_edx": "js/src/lang_edx",
            // end of Annotation tool files

            // externally hosted files
            "mathjax": "//cdn.mathjax.org/mathjax/2.6-latest/MathJax.js?config=TeX-MML-AM_SVG&delayStartupUntil=configured", // jshint ignore:line
            "youtube": [
                // youtube URL does not end in ".js". We add "?noext" to the path so
                // that require.js adds the ".js" to the query component of the URL,
                // and leaves the path component intact.
                "//www.youtube.com/player_api?noext",
                // if youtube fails to load, fallback on a local file
                // so that require doesn't fall over
                "js/src/youtube_fallback"
            ]
        },
        shim: {
            "gettext": {
                exports: "gettext"
            },
            "date": {
                exports: "Date"
            },
            "jquery-migrate": ['jquery'],
            "jquery.ui": {
                deps: ["jquery"],
                exports: "jQuery.ui"
            },
            "jquery.form": {
                deps: ["jquery"],
                exports: "jQuery.fn.ajaxForm"
            },
            "jquery.markitup": {
                deps: ["jquery"],
                exports: "jQuery.fn.markitup"
            },
            "jquery.leanmodal": {
                deps: ["jquery"],
                exports: "jQuery.fn.leanModal"
            },
            "jquery.ajaxQueue": {
                deps: ["jquery"],
                exports: "jQuery.fn.ajaxQueue"
            },
            "jquery.smoothScroll": {
                deps: ["jquery"],
                exports: "jQuery.fn.smoothScroll"
            },
            "jquery.cookie": {
                deps: ["jquery"],
                exports: "jQuery.fn.cookie"
            },
            "jquery.qtip": {
                deps: ["jquery"],
                exports: "jQuery.fn.qtip"
            },
            "jquery.scrollTo": {
                deps: ["jquery"],
                exports: "jQuery.fn.scrollTo"
            },
            "jquery.flot": {
                deps: ["jquery"],
                exports: "jQuery.fn.plot"
            },
            "jquery.fileupload": {
                deps: ["jquery.ui", "jquery.iframe-transport"],
                exports: "jQuery.fn.fileupload"
            },
            "jquery.fileupload-process": {
                deps: ["jquery.fileupload"]
            },
            "jquery.fileupload-validate": {
                deps: ["jquery.fileupload"]
            },
            "jquery.inputnumber": {
                deps: ["jquery"],
                exports: "jQuery.fn.inputNumber"
            },
            "jquery.tinymce": {
                deps: ["jquery", "tinymce"],
                exports: "jQuery.fn.tinymce"
            },
            "datepair": {
                deps: ["jquery.ui", "jquery.timepicker"]
            },
            "underscore": {
                exports: "_"
            },
            "backbone": {
                deps: ["underscore", "jquery"],
                exports: "Backbone"
            },
            "backbone.associations": {
                deps: ["backbone"],
                exports: "Backbone.Associations"
            },
            "backbone.paginator": {
                deps: ["backbone"],
                exports: "Backbone.Paginator"
            },
            "youtube": {
                exports: "YT"
            },
            "codemirror": {
                exports: "CodeMirror"
            },
            "codemirror/stex": {
                deps: ["codemirror"]
            },
            "tinymce": {
                exports: "tinymce"
            },
            "lang_edx": {
                deps: ["jquery"]
            },
            "mathjax": {
                exports: "MathJax",
                init: function() {
                    window.MathJax.Hub.Config({
                        tex2jax: {
                            inlineMath: [
                                ["\\(","\\)"],
                                ['[mathjaxinline]','[/mathjaxinline]']
                            ],
                            displayMath: [
                                ["\\[","\\]"],
                                ['[mathjax]','[/mathjax]']
                            ]
                        }
                });
                // In order to eliminate all flashing during interactive
                // preview, it is necessary to set processSectionDelay to 0
                // (remove delay between input and output phases). This
                // effectively disables fast preview, regardless of
                // the fast preview setting as shown in the context menu.
                window.MathJax.Hub.processSectionDelay = 0;
                window.MathJax.Hub.Configured();
                }
            },
            "URI": {
                exports: "URI"
            },
            "tooltip_manager": {
                deps: ["jquery", "underscore"]
            },
            "jquery.immediateDescendents": {
                deps: ["jquery"]
            },
            "xblock/core": {
                exports: "XBlock",
                deps: ["jquery", "jquery.immediateDescendents"]
            },
            "xblock/runtime.v1": {
                exports: "XBlock",
                deps: ["xblock/core"]
            },
            "coffee/src/main": {
                deps: ["coffee/src/ajax_prefix"]
            },
            "js/src/logger": {
                exports: "Logger",
                deps: ["coffee/src/ajax_prefix"]
            },
            "modernizr": {
                exports: "Modernizr"
            },
            "afontgarde": {
                exports: "AFontGarde"
            },

            // the following are all needed for annotation tools
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
            "ova":{
                exports: "ova",
                deps: ["annotator", "annotator-harvardx", "video.dev", "vjs.youtube",
                       "rangeslider", "share-annotator", "richText-annotator", "reply-annotator",
                       "tags-annotator", "flagging-annotator", "grouping-annotator", "diacritic-annotator",
                       "jquery-Watch", "catch", "handlebars", "URI"]
            },
            "osda":{
                exports: "osda",
                deps: ["annotator", "annotator-harvardx", "video.dev", "vjs.youtube",
                       "rangeslider", "share-annotator", "richText-annotator", "reply-annotator",
                       "tags-annotator", "flagging-annotator", "grouping-annotator", "diacritic-annotator",
                       "openseadragon", "jquery-Watch", "catch", "handlebars", "URI"]
            }
            // end of annotation tool files
        }
    });
}).call(this, require, define);
