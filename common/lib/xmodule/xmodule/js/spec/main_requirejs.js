(function(requirejs) {
    requirejs.config({
        paths: {
            "moment": "xmodule/include/common_static/js/vendor/moment.min",
            "modernizr": "xmodule/include/common_static/edx-pattern-library/js/modernizr-custom",
            "afontgarde": "xmodule/include/common_static/edx-pattern-library/js/afontgarde",
            "edxicons": "xmodule/include/common_static/edx-pattern-library/js/edx-icons",
            "draggabilly": "xmodule/include/common_static/js/vendor/draggabilly"
        },
        "moment": {
            exports: "moment"
        },
        "modernizr": {
            exports: "Modernizr"
        },
        "afontgarde": {
            exports: "AFontGarde"
        }
    });

}).call(this, RequireJS.requirejs);
