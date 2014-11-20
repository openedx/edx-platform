require.config({
    baseUrl: '',
    waitSeconds: 60,
    paths: {
        'backbone':             '../../common/static/js/vendor/backbone-min',
        'gettext':              '/i18n',
        'jquery':               '../../common/static/js/vendor/jquery.min',
        'underscore':           '../../common/static/js/vendor/underscore-min',
        'underscore.string':    '../../common/static/js/vendor/underscore.string.min'
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
