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
                    'lms/static/sass/application.css': 'lms/static/sass/application.scss'
                }
            }
        }
    });

    grunt.registerTask('default', [
    ]);
};
