'use strict';

module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        sass: {
            lms: {
                options: {
                    loadPath: [
                        'bower_components'
                    ]
                },
                files: {
                    'lms/static/sass/application-extend1-rtl.css': 'lms/static/sass/application-extend1-rtl.scss',
                    'lms/static/sass/application-extend1.css': 'lms/static/sass/application-extend1.scss',
                    'lms/static/sass/application-extend2-rtl.css': 'lms/static/sass/application-extend2-rtl.scss',
                    'lms/static/sass/application-extend2.css': 'lms/static/sass/application-extend2.scss',
                    'lms/static/sass/application.css': 'lms/static/sass/application.scss'
                }
            }
        }
    });

    grunt.registerTask('default', [
    ]);
};
