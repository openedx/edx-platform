var require = {
    /* The baseURL is overridden when using RequireJS optimizer,
    * but is necessary for local development.
    */
    baseUrl: "/static/",
    waitSeconds: 60,
    paths: {
        'backbone':             'js/vendor/backbone-min',
        'gettext':              '/i18n',
        'jquery':               'js/vendor/jquery.min',
        'jquery.cookie':        'js/vendor/jquery.cookie',
        'underscore':           'js/vendor/underscore-min',
        'underscore.string':    'js/vendor/underscore.string.min'
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

        'underscore': {
            exports: '_'
        }
    }
};
