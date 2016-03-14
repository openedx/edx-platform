(function(requirejs) {
    requirejs.config({
        paths: {
            "moment": "xmodule/include/common_static/js/vendor/moment.min"
        },
        "moment": {
            exports: "moment"
        }
    });

}).call(this, RequireJS.requirejs);
