;(function (require, define) {
    var paths = {}, config;

    // jquery, underscore may already have been loaded and we do not want to load
    // them a second time. Check if it is the case and use the global var in requireJS config.
    if (window.jQuery) {
        define("jquery", [], function() {return window.jQuery;});
    } else {
        paths.jquery = "js/vendor/jquery.min";
    }
    if (window._) {
        define("underscore", [], function() {return window._;});
    } else {
        paths.jquery = "js/vendor/underscore-min";
    }

    config = {
        // NOTE: baseUrl has been previously set in lms/static/templates/main.html
        waitSeconds: 60,
        paths: {
          "annotator_1.2.9": "js/vendor/edxnotes/annotator-full.min",
          "date": "js/vendor/date",
          "backbone": "js/vendor/backbone-min"
        },
        shim: {
          "annotator_1.2.9": {
            exports: "Annotator"
          },
          "date": {
              exports: "Date"
          },
          "jquery": {
              exports: "$"
          },
          "underscore": {
              exports: "_"
          },
          "backbone": {
              deps: ["underscore", "jquery"],
              exports: "Backbone"
          }
        },
        map: {
          "js/edxnotes/views/notes": {
            "annotator": "annotator_1.2.9"
          },
          "js/edxnotes/views/shim": {
            "annotator": "annotator_1.2.9"
          }
        }
    };

    for (var key in paths) {
      if ({}.hasOwnProperty.call(paths, key)) {
        config.paths[key] = paths[key];
      }
    }
    require.config(config);
}).call(this, require || RequireJS.require, define || RequireJS.define);
