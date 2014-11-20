require.config({
    paths: {
        jquery:         '../../common/static/js/vendor/jquery.min',
        underscore:     '../../common/static/js/vendor/underscore-min',
        backbone:       '../../common/static/js/vendor/backbone-min'
    },
    shim: {
        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },

        underscore: {
            exports: '_'
        }
    }
});