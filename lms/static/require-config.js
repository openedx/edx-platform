;(function (require) {
    require.config({
        // NOTE: baseUrl has been previously set in lms/static/templates/main.html
        waitSeconds: 60,
        paths: {
          'annotator_1.2.9': 'js/vendor/edxnotes/annotator-full.min'
        },
        map: {
          'js/edxnotes/notes': {
            'annotator': 'annotator_1.2.9'
          },
          'js/edxnotes/shim': {
            'annotator': 'annotator_1.2.9'
          }
        }
    });
}).call(this, require || RequireJS.require);
