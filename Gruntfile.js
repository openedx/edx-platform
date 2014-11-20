'use strict';

module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);
    require('time-grunt')(grunt);

    grunt.initConfig({
        clean: {
            lms: {
                src: [
                    // Sass-generated files
                    'lms/static/sass/application-extend1-rtl.css',
                    'lms/static/sass/application-extend1.css',
                    'lms/static/sass/application-extend2-rtl.css',
                    'lms/static/sass/application-extend2.css',
                    'lms/static/sass/application.css',

                    // Concat-generated files
                    'lms/static/css/lms-style-vendor.css',
                    'lms/static/css/lms-style-vendor-tinymce-content.css',
                    'lms/static/css/lms-style-vendor-tinymce-skin.css',
                    'lms/static/css/lms-style-app.css',
                    'lms/static/css/lms-style-app-extend2.css',
                    'lms/static/css/lms-style-app-rtl.css',
                    'lms/static/css/lms-style-app-extend2-rtl.css',
                    'lms/static/css/lms-style-course-vendor.css',
                    'lms/static/css/lms-style-course.css',
                    'lms/static/css/lms-style-course-rtl.css',
                    'lms/static/css/lms-style-xmodule-annotations.css'
                ]
            }
        },

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
        },

        concat: {
            lms: {
                files: {
                    'lms/static/css/lms-style-vendor.css': [
                        'lms/static/css/vendor/font-awesome.css',
                        'lms/static/css/vendor/jquery.qtip.min.css',
                        'lms/static/css/vendor/responsive-carousel/responsive-carousel.css',
                        'lms/static/css/vendor/responsive-carousel/responsive-carousel.slide.css'
                    ],
                    'lms/static/css/lms-style-vendor-tinymce-content.css': [
                        'lms/static/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/content.min.css'
                    ],
                    'lms/static/css/lms-style-vendor-tinymce-skin.css': [
                        'lms/static/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/skin.min.css'
                    ],
                    'lms/static/css/lms-style-app.css': [
                        'lms/static/sass/application.css',
                        'lms/static/sass/ie.css'
                    ],
                    'lms/static/css/lms-style-app-extend1.css': [
                        'lms/static/sass/application-extend1.css'
                    ],
                    'lms/static/css/lms-style-app-extend2.css': [
                        'lms/static/sass/application-extend2.css'
                    ],
                    'lms/static/css/lms-style-app-rtl.css': [
                        'lms/static/sass/application-rtl.css',
                        'lms/static/sass/ie-rtl.css'
                    ],
                    'lms/static/css/lms-style-app-extend1-rtl.css': [
                        'lms/static/sass/application-extend1-rtl.css'
                    ],
                    'lms/static/css/lms-style-app-extend2-rtl.css': [
                        'lms/static/sass/application-extend2-rtl.css'
                    ],
                    'lms/static/css/lms-style-course-vendor.css': [
                        'lms/static/js/vendor/CodeMirror/codemirror.css',
                        'lms/static/css/vendor/jquery.treeview.css',
                        'lms/static/css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css'
                    ],
                    'lms/static/css/lms-style-course.css': [
                        'lms/static/sass/course.css',
                        'lms/static/xmodule/modules.css'
                    ],
                    'lms/static/css/lms-style-course-rtl.css': [
                        'lms/static/sass/course-rtl.css',
                        'lms/static/xmodule/modules.css'
                    ],
                    'lms/static/css/lms-style-xmodule-annotations.css': [
                        'lms/static/css/vendor/ova/annotator.css',
                        'lms/static/css/vendor/ova/edx-annotator.css',
                        'lms/static/css/vendor/ova/video-js.min.css',
                        'lms/static/css/vendor/ova/rangeslider.css',
                        'lms/static/css/vendor/ova/share-annotator.css',
                        'lms/static/css/vendor/ova/richText-annotator.css',
                        'lms/static/css/vendor/ova/tags-annotator.css',
                        'lms/static/css/vendor/ova/flagging-annotator.css',
                        'lms/static/css/vendor/ova/diacritic-annotator.css',
                        'lms/static/css/vendor/ova/grouping-annotator.css',
                        'lms/static/css/vendor/ova/ova.css',
                        'lms/static/js/vendor/ova/catch/css/main.css'
                    ]
                }
            }
        }
    });

    grunt.registerTask('lms', [
        'clean:lms',
        'sass:lms',
        'concat:lms'
    ]);
};
