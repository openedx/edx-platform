/* globals _, requirejs */
/* eslint-disable quote-props */

(function(require, define) {
    'use strict';

    var defineDependency;

    // We do not wish to bundle common libraries (that may also be used by non-RequireJS code on the page
    // into the optimized files. Therefore load these libraries through script tags and explicitly define them.
    // Note that when the optimizer executes this code, window will not be defined.
    if (window) {
        defineDependency = function(globalName, name, noShim) {
            var getGlobalValue = function() {
                    var globalNamePath = globalName.split('.'),
                        result = window,
                        i;
                    for (i = 0; i < globalNamePath.length; i++) {
                        result = result[globalNamePath[i]];
                    }
                    return result;
                },
                globalValue = getGlobalValue();
            if (globalValue) {
                if (noShim) {
                    define(name, {});
                } else {
                    define(name, [], function() { return globalValue; });
                }
            } else {
                console.error('Expected library to be included on page, but not found on window object: ' + name);
            }
        };
        defineDependency('jQuery', 'jquery');
        defineDependency('jQuery', 'jquery-migrate');
        defineDependency('_', 'underscore');
        defineDependency('s', 'underscore.string');
        // Underscore.string no longer installs itself directly on '_'. For compatibility with existing
        // code, add it to '_' with its previous name.
        if (window._ && window.s) {
            window._.str = window.s;
        }
        defineDependency('gettext', 'gettext');
        defineDependency('Logger', 'logger');
        defineDependency('URI', 'URI');
        defineDependency('jQuery.url', 'jquery.url');
        defineDependency('Backbone', 'backbone');

        // Add the UI Toolkit helper classes that have been installed in the 'edx' namespace
        defineDependency('edx.HtmlUtils', 'edx-ui-toolkit/js/utils/html-utils');
        defineDependency('edx.StringUtils', 'edx-ui-toolkit/js/utils/string-utils');

        // utility.js adds two functions to the window object, but does not return anything
        defineDependency('isExternal', 'utility', true);
    }

    require.config({
        // NOTE: baseUrl has been previously set in lms/templates/main.html
        waitSeconds: 60,
        paths: {
            'annotator_1.2.9': 'js/vendor/edxnotes/annotator-full.min',
            'date': 'js/vendor/date',
            moment: 'common/js/vendor/moment-with-locales',
            'moment-timezone': 'common/js/vendor/moment-timezone-with-data',
            'text': 'js/vendor/requirejs/text',
            'logger': 'js/src/logger',
            'backbone': 'common/js/vendor/backbone',
            'backbone-super': 'js/vendor/backbone-super',
            'backbone.paginator': 'common/js/vendor/backbone.paginator',
            'underscore': 'common/js/vendor/underscore',
            'underscore.string': 'common/js/vendor/underscore.string',
            // The jquery-migrate library was added in upgrading from
            // jQuery 1.7.x to 2.2.x.  This config allows developers
            // to depend on 'jquery' which opaquely requires both
            // libraries.
            'jquery': 'common/js/vendor/jquery',
            'jquery-migrate': 'common/js/vendor/jquery-migrate',
            'jquery.scrollTo': 'common/js/vendor/jquery.scrollTo',
            'jquery.cookie': 'js/vendor/jquery.cookie',
            'jquery.timeago': 'js/vendor/jquery.timeago',
            'jquery.url': 'js/vendor/url.min',
            'jquery.ui': 'js/vendor/jquery-ui.min',
            'jquery.iframe-transport': 'js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',
            'jquery.fileupload': 'js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'URI': 'js/vendor/URI.min',
            'string_utils': 'js/src/string_utils',
            'utility': 'js/src/utility',
            'draggabilly': 'js/vendor/draggabilly',

            // Files needed by OVA
            'annotator': 'js/vendor/ova/annotator-full',
            'annotator-harvardx': 'js/vendor/ova/annotator-full-firebase-auth',
            'video.dev': 'js/vendor/ova/video.dev',
            'vjs.youtube': 'js/vendor/ova/vjs.youtube',
            'rangeslider': 'js/vendor/ova/rangeslider',
            'share-annotator': 'js/vendor/ova/share-annotator',
            'richText-annotator': 'js/vendor/ova/richText-annotator',
            'reply-annotator': 'js/vendor/ova/reply-annotator',
            'grouping-annotator': 'js/vendor/ova/grouping-annotator',
            'tags-annotator': 'js/vendor/ova/tags-annotator',
            'diacritic-annotator': 'js/vendor/ova/diacritic-annotator',
            'flagging-annotator': 'js/vendor/ova/flagging-annotator',
            'jquery-Watch': 'js/vendor/ova/jquery-Watch',
            'openseadragon': 'js/vendor/ova/openseadragon',
            'osda': 'js/vendor/ova/OpenSeaDragonAnnotation',
            'ova': 'js/vendor/ova/ova',
            'catch': 'js/vendor/ova/catch/js/catch',
            'handlebars': 'js/vendor/ova/catch/js/handlebars-1.1.2',
            'tinymce': 'js/vendor/tinymce/js/tinymce/tinymce.full.min',
            'jquery.tinymce': 'js/vendor/tinymce/js/tinymce/jquery.tinymce.min',
            'picturefill': 'common/js/vendor/picturefill'
            // end of files needed by OVA
        },
        shim: {
            'annotator_1.2.9': {
                deps: ['jquery'],
                exports: 'Annotator'
            },
            'date': {
                exports: 'Date'
            },
            'jquery': {
                exports: 'jQuery'
            },
            'jquery-migrate': ['jquery'],
            'jquery.cookie': {
                deps: ['jquery'],
                exports: 'jQuery.fn.cookie'
            },
            'jquery.timeago': {
                deps: ['jquery'],
                exports: 'jQuery.timeago'
            },
            'jquery.url': {
                deps: ['jquery'],
                exports: 'jQuery.url'
            },
            'jquery.fileupload': {
                deps: ['jquery.ui', 'jquery.iframe-transport'],
                exports: 'jQuery.fn.fileupload'
            },
            'jquery.tinymce': {
                deps: ['jquery', 'tinymce'],
                exports: 'jQuery.fn.tinymce'
            },
            'backbone.paginator': {
                deps: ['backbone'],
                exports: 'Backbone.PageableCollection'
            },
            'backbone-super': {
                deps: ['backbone']
            },
            'string_utils': {
                deps: ['underscore'],
                exports: 'interpolate_text'
            },
            // Needed by OVA
            'video.dev': {
                exports: 'videojs'
            },
            'vjs.youtube': {
                deps: ['video.dev']
            },
            'rangeslider': {
                deps: ['video.dev']
            },
            'annotator': {
                exports: 'Annotator'
            },
            'annotator-harvardx': {
                deps: ['annotator']
            },
            'share-annotator': {
                deps: ['annotator']
            },
            'richText-annotator': {
                deps: ['annotator', 'tinymce']
            },
            'reply-annotator': {
                deps: ['annotator']
            },
            'tags-annotator': {
                deps: ['annotator']
            },
            'diacritic-annotator': {
                deps: ['annotator']
            },
            'flagging-annotator': {
                deps: ['annotator']
            },
            'grouping-annotator': {
                deps: ['annotator']
            },
            'ova': {
                exports: 'ova',
                deps: [
                    'annotator', 'annotator-harvardx', 'video.dev', 'vjs.youtube', 'rangeslider', 'share-annotator',
                    'richText-annotator', 'reply-annotator', 'tags-annotator', 'flagging-annotator',
                    'grouping-annotator', 'diacritic-annotator', 'jquery-Watch', 'catch', 'handlebars', 'URI'
                ]
            },
            'osda': {
                exports: 'osda',
                deps: [
                    'annotator', 'annotator-harvardx', 'video.dev', 'vjs.youtube', 'rangeslider', 'share-annotator',
                    'richText-annotator', 'reply-annotator', 'tags-annotator', 'flagging-annotator',
                    'grouping-annotator', 'diacritic-annotator', 'openseadragon', 'jquery-Watch', 'catch', 'handlebars',
                    'URI'
                ]
            },
            'tinymce': {
                exports: 'tinymce'
            },
            // End of needed by OVA
            'moment': {
                exports: 'moment'
            },
            'moment-timezone': {
                exports: 'moment',
                deps: ['moment']
            },
            // Because Draggabilly is being used by video code, the namespaced version of
            // require is not being recognized. Therefore the library is being added to the
            // global namespace instead of being registered in require.
            'draggabilly': {
                exports: 'Draggabilly'
            }
        }
    });
}).call(this, require || RequireJS.require, define || RequireJS.define);
