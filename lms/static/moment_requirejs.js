(function(requirejs) {
    requirejs.config({
        paths: {
            "moment": "/base/xmodule_js/common_static/js/vendor/moment.min"
        },
        shim:{
            "moment": {
                exports: "moment"
            }
        }
    });

}).call(this, RequireJS.requirejs);
