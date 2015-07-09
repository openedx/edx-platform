(function(requirejs, define) {
    requirejs.config({
        paths: {
            'moment': 'common_static/js/vendor/moment.min'
        },
        shim: {
            'moment': {
                exports: 'moment'
            }
        }
    });

}).call(this, RequireJS.requirejs, define);
