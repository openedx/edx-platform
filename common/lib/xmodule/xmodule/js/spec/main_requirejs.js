(function(requirejs) {
    requirejs.config({
        baseUrl: '/base/',
        paths: {
            "moment": "common_static/js/vendor/moment.min",
            "modernizr": "common_static/edx-pattern-library/js/modernizr-custom",
            "afontgarde": "common_static/edx-pattern-library/js/afontgarde",
            "edxicons": "common_static/edx-pattern-library/js/edx-icons",
            "draggabilly": "common_static/js/vendor/draggabilly"
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
