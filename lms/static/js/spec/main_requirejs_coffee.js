(function(requirejs) {
    'use strict';
    requirejs.config({
        baseUrl: '/base/',
        paths: {
            "moment": "xmodule_js/common_static/js/vendor/moment.min",
            "modernizr": "xmodule_js/common_static/edx-pattern-library/js/modernizr-custom",
            "afontgarde": "xmodule_js/common_static/edx-pattern-library/js/afontgarde",
            "edxicons": "xmodule_js/common_static/edx-pattern-library/js/edx-icons",
            "draggabilly": "xmodule_js/common_static/js/vendor/draggabilly"
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

}).call(this, requirejs, define); // jshint ignore:line
