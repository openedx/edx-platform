var require = {
    /* The baseURL is overridden by RequireJS optimizer
    * and in the main Mako template that loads the config.
    */
    waitSeconds: 60,
    paths: {
        'backbone':             'js/vendor/backbone-min',
        'gettext':              '/i18n',
        'jquery':               'js/vendor/jquery.min',
        'jquery.cookie':        'js/vendor/jquery.cookie',
        'jquery.url':           'js/vendor/url.min',
        'text':                 'js/vendor/text',
        'underscore':           'js/vendor/underscore-min',
        'underscore.string':    'js/vendor/underscore.string.min',

        // This module defines some global functions.
        // TODO: replace these with RequireJS-compatible modules
        'utility':              'js/src/utility'
    },
    shim: {
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },

        'gettext': {
            exports: 'gettext'
        },

        'jquery.cookie': {
            deps: ['jquery'],
            exports: 'jQuery.fn.cookie'
        },

        'jquery.url': {
            deps: ['jquery'],
            exports: 'jQuery.url'
        },

        'underscore': {
            exports: '_'
        }
    }
};
