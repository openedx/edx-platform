;(function (require) {
    require.config({
        // NOTE: baseUrl has been previously set in lms/static/templates/main.html
        waitSeconds: 60,
        paths: {
          "annotator_1.2.9": "js/vendor/edxnotes/annotator-full.min",
          "date": "js/vendor/date",
          "jquery": "js/vendor/jquery.min",
          "underscore": "js/vendor/underscore-min",
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
    });
}).call(this, require || RequireJS.require);
