(function(requirejs) {
    requirejs.config({
        paths: {
            "draggabilly": "xmodule/include/common_static/js/vendor/draggabilly.pkgd",
            "moment": "xmodule/include/common_static/js/vendor/moment.min"
        },
        "draggabilly": {
            exports: "Draggabilly"
        },
        "moment": {
            exports: "moment"
        }
    });

}).call(this, RequireJS.requirejs);
