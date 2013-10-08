require =
    baseUrl: "/suite/cms/include"
    paths:
        "jquery": "xmodule_js/common_static/js/vendor/jquery.min",
        "jquery.ui" : "xmodule_js/common_static/js/vendor/jquery-ui.min",
        "jquery.cookie": "xmodule_js/common_static/js/vendor/jquery.cookie",
        "underscore": "xmodule_js/common_static/js/vendor/underscore-min",
        "underscore.string": "xmodule_js/common_static/js/vendor/underscore.string.min",
        "backbone": "xmodule_js/common_static/js/vendor/backbone-min",
        "backbone.associations": "xmodule_js/common_static/js/vendor/backbone-associations-min",
        "jquery.timepicker": "xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker",
        "jquery.leanModal": "xmodule_js/common_static/js/vendor/jquery.leanModal.min",
        "jquery.scrollTo": "xmodule_js/common_static/js/vendor/jquery.scrollTo-1.4.2-min",
        "jquery.flot": "xmodule_js/common_static/js/vendor/flot/jquery.flot.min",
        "jquery.form": "xmodule_js/common_static/js/vendor/jquery.form",
        "jquery.inputnumber": "xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill",
        "sinon": "xmodule_js/common_static/js/vendor/sinon-1.7.1",
        "xmodule": "xmodule_js/src/xmodule",
        "gettext": "xmodule_js/common_static/js/test/i18n",
        "utility": "xmodule_js/common_static/js/src/utility",
        "codemirror": "xmodule_js/common_static/js/vendor/CodeMirror/codemirror"
    shim:
        "gettext":
            exports: "gettext"
        "jquery.ui":
            deps: ["jquery"]
            exports: "jQuery.ui"
        "jquery.form":
            deps: ["jquery"]
            exports: "jQuery.fn.ajaxForm"
        "jquery.inputnumber":
            deps: ["jquery"]
            exports: "jQuery.fn.inputNumber"
        "jquery.leanModal":
            deps: ["jquery"],
            exports: "jQuery.fn.leanModal"
        "jquery.cookie":
            deps: ["jquery"],
            exports: "jQuery.fn.cookie"
        "jquery.scrollTo":
            deps: ["jquery"],
            exports: "jQuery.fn.scrollTo"
        "jquery.flot":
            deps: ["jquery"],
            exports: "jQuery.fn.plot"
        "underscore":
            exports: "_"
        "backbone":
            deps: ["underscore", "jquery"],
            exports: "Backbone"
        "backbone.associations":
            deps: ["backbone"],
            exports: "Backbone.Associations"
        "xmodule":
            exports: "XModule"
        "sinon":
            exports: "sinon"
        "codemirror":
            exports: "CodeMirror"
    # load these automatically
    deps: ["js/base", "coffee/src/main"]
