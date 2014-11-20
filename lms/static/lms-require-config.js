require.config({
    baseUrl: '',
    waitSeconds: 60,
    paths: {
        'backbone':             'js/vendor/backbone-min',
        'gettext':              '/i18n',
        'jquery':               'js/vendor/jquery.min',
        'underscore':           'js/vendor/underscore-min',
        'underscore.string':    'js/vendor/underscore.string.min'
    },
    shim: {
        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },

        gettext: {
            exports: 'gettext'
        },

        underscore: {
            exports: '_'
        }
    }
});
