(function(requirejs) {
    'use strict';
    requirejs.config({
        baseUrl: '/base/',
        paths: {
            "moment": "xmodule_js/common_static/js/vendor/moment.min",
            "modernizr": "edx-pattern-library/js/modernizr-custom",
            "afontgarde": "edx-pattern-library/js/afontgarde",
            "edxicons": "edx-pattern-library/js/edx-icons",
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
