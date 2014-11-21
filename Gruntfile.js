'use strict';

var fs = require('fs');
var util = require('util');

module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);
    require('time-grunt')(grunt);

    var config = {
        bower: 'bower_components',
        lms: 'lms/static',
        studio: 'cms/static',
        common: 'common/static',
        theme: grunt.option('theme')
    };

    if (config.theme) {
        if (fs.existsSync(config.theme)) {
            grunt.log.writeln(util.format('Theme configured in: %s', config.theme));
            config.theme += '/static';
        }
        else {
            grunt.fail.warn(util.format('The theme directory (%s) does not exist', config.theme));
        }
    }

    grunt.initConfig({
        c: config,

        watch: {
            'sass_lms': {
                files: [
                    '<%= c.lms %>/sass/**/*.scss',
                    '<%= c.common %>/sass/**/*.scss',
                    '<%= c.theme %>/sass/**/*.scss'
                ],
                tasks: [
                    'sass:lms',
                    'concat:lms'
                ]
            },

            'sass_studio': {
                files: [
                    '<%= c.studio %>/sass/**/*.scss',
                    '<%= c.common %>/sass/**/*.scss'
                ],
                tasks: [
                    'sass:studio',
                    'concat:studio'
                ]
            },

            'coffee_common': {
                files: [
                    '<%= c.common %>/coffee/**/*.coffee',
                    '<%= c.common %>/xmodule/**/*.coffee'
                ],
                tasks: [
                    'coffee:common'
                ]
            },

            'coffee_lms': {
                files: function () {
                    var paths = [
                        '<%= c.lms %>/coffee/**/*.coffee'
                    ];

                    if (config.theme) {
                        paths.push('<%= c.theme %>/coffee/**/*.coffee');
                    }

                    return paths;
                }(),
                tasks: [
                    'coffee:lms'
                ]
            },

            'coffee_studio': {
                files: [
                    '<%= c.studio %>/coffee/**/*.coffee'
                ],
                tasks: [
                    'coffee:studio'
                ]
            }
        },

        clean: {
            lms: {
                src: [
                    // Sass-generated files
                    '<%= c.lms %>/sass/application-extend1-rtl.css',
                    '<%= c.lms %>/sass/application-extend1.css',
                    '<%= c.lms %>/sass/application-extend2-rtl.css',
                    '<%= c.lms %>/sass/application-extend2.css',
                    '<%= c.lms %>/sass/application.css',
                    '<%= c.lms %>/sass/course-rtl.css',
                    '<%= c.lms %>/sass/course.css',
                    '<%= c.lms %>/sass/ie.css',


                    // Concat-generated files
                    '<%= c.lms %>/css/lms-style-vendor.css',
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-content.css',
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-skin.css',
                    '<%= c.lms %>/css/lms-style-app.css',
                    '<%= c.lms %>/css/lms-style-app-extend2.css',
                    '<%= c.lms %>/css/lms-style-app-rtl.css',
                    '<%= c.lms %>/css/lms-style-app-extend2-rtl.css',
                    '<%= c.lms %>/css/lms-style-course-vendor.css',
                    '<%= c.lms %>/css/lms-style-course.css',
                    '<%= c.lms %>/css/lms-style-course-rtl.css',
                    '<%= c.lms %>/css/lms-style-xmodule-annotations.css'
                ]
            },
            studio: {
                src: [
                    // Sass-generated files
                    '<%= c.studio %>/sass/style-app.css',
                    '<%= c.studio %>/sass/style-app-rtl.css',
                    '<%= c.studio %>/sass/style-app-extend1.css',
                    '<%= c.studio %>/sass/style-app-extend1-rtl.css',
                    '<%= c.studio %>/sass/style-xmodule.css',
                    '<%= c.studio %>/sass/style-xmodule-rtl.css',

                    // Concat-generated files
                    '<%= c.studio %>/css/cms-style-vendor.css',
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-content.css',
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-skin.css',
                    '<%= c.studio %>/css/cms-style-app.css',
                    '<%= c.studio %>/css/cms-style-app-rtl.css',
                    '<%= c.studio %>/css/cms-style-app-extend1.css',
                    '<%= c.studio %>/css/cms-style-app-extend1-rtl.css',
                    '<%= c.studio %>/css/cms-style-xmodule.css',
                    '<%= c.studio %>/css/cms-style-xmodule-rtl.css',
                    '<%= c.studio %>/css/cms-style-xmodule-annotations.css'
                ]
            }
        },

        sass: {
            lms: {
                options: {
                    includePaths: [
                        '<%= c.bower %>',
                        '<%= c.bower %>/bi-app-sass',
                        // This is for xmodule sass files
                        '<%= c.common %>',
                        '<%= c.common %>/sass',
                        '<%= c.theme %>/sass'
                    ]
               },
                files: {
                    '<%= c.lms %>/sass/application-extend1-rtl.css': '<%= c.lms %>/sass/application-extend1-rtl.scss',
                    '<%= c.lms %>/sass/application-extend1.css': '<%= c.lms %>/sass/application-extend1.scss',
                    '<%= c.lms %>/sass/application-extend2-rtl.css': '<%= c.lms %>/sass/application-extend2-rtl.scss',
                    '<%= c.lms %>/sass/application-extend2.css': '<%= c.lms %>/sass/application-extend2.scss',
                    '<%= c.lms %>/sass/application.css': '<%= c.lms %>/sass/application.scss',
                    '<%= c.lms %>/sass/application-rtl.css': '<%= c.lms %>/sass/application-rtl.scss',
                    '<%= c.lms %>/sass/course-rtl.css': '<%= c.lms %>/sass/course-rtl.scss',
                    '<%= c.lms %>/sass/course.css': '<%= c.lms %>/sass/course.scss',
                    '<%= c.lms %>/sass/ie.css': '<%= c.lms %>/sass/ie.scss',
                }
            },
            studio: {
                options: {
                    includePaths: [
                        '<%= c.bower %>',
                        '<%= c.bower %>/bi-app-sass',
                        // This is for xmodule sass files
                        '<%= c.common %>',
                        '<%= c.common %>/sass'
                    ]
                },
                files: {
                    '<%= c.studio %>/sass/style-app.css': '<%= c.studio %>/sass/style-app.scss',
                    '<%= c.studio %>/sass/style-app-rtl.css': '<%= c.studio %>/sass/style-app-rtl.scss',
                    '<%= c.studio %>/sass/style-app-extend1.css': '<%= c.studio %>/sass/style-app-extend1.scss',
                    '<%= c.studio %>/sass/style-app-extend1-rtl.css': '<%= c.studio %>/sass/style-app-extend1-rtl.scss',
                    '<%= c.studio %>/sass/style-xmodule.css': '<%= c.studio %>/sass/style-xmodule.scss',
                    '<%= c.studio %>/sass/style-xmodule-rtl.css': '<%= c.studio %>/sass/style-xmodule-rtl.scss'
                }
            }
        },

        concat: {
            lms: {
                files: {
                    '<%= c.lms %>/css/lms-style-vendor.css': [
                        '<%= c.bower %>/font-awesome/css/font-awesome.css',
                        '<%= c.lms %>/css/vendor/jquery.qtip.min.css',
                        '<%= c.lms %>/css/vendor/responsive-carousel/responsive-carousel.css',
                        '<%= c.lms %>/css/vendor/responsive-carousel/responsive-carousel.slide.css'
                    ],
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-content.css': [
                        '<%= c.lms %>/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/content.min.css'
                    ],
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-skin.css': [
                        '<%= c.lms %>/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/skin.min.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app.css': [
                        '<%= c.lms %>/sass/application.css',
                        '<%= c.lms %>/sass/ie.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app-extend1.css': [
                        '<%= c.lms %>/sass/application-extend1.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app-extend2.css': [
                        '<%= c.lms %>/sass/application-extend2.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app-rtl.css': [
                        '<%= c.lms %>/sass/application-rtl.css',
                        '<%= c.lms %>/sass/ie-rtl.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app-extend1-rtl.css': [
                        '<%= c.lms %>/sass/application-extend1-rtl.css'
                    ],
                    '<%= c.lms %>/css/lms-style-app-extend2-rtl.css': [
                        '<%= c.lms %>/sass/application-extend2-rtl.css'
                    ],
                    '<%= c.lms %>/css/lms-style-course-vendor.css': [
                        '<%= c.lms %>/js/vendor/CodeMirror/codemirror.css',
                        '<%= c.lms %>/css/vendor/jquery.treeview.css',
                        '<%= c.lms %>/css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css'
                    ],
                    '<%= c.lms %>/css/lms-style-course.css': [
                        '<%= c.lms %>/sass/course.css',
                        '<%= c.lms %>/xmodule/modules.css'
                    ],
                    '<%= c.lms %>/css/lms-style-course-rtl.css': [
                        '<%= c.lms %>/sass/course-rtl.css',
                        '<%= c.lms %>/xmodule/modules.css'
                    ],
                    '<%= c.lms %>/css/lms-style-xmodule-annotations.css': [
                        '<%= c.lms %>/css/vendor/ova/annotator.css',
                        '<%= c.lms %>/css/vendor/ova/edx-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/video-js.min.css',
                        '<%= c.lms %>/css/vendor/ova/rangeslider.css',
                        '<%= c.lms %>/css/vendor/ova/share-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/richText-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/tags-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/flagging-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/diacritic-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/grouping-annotator.css',
                        '<%= c.lms %>/css/vendor/ova/ova.css',
                        '<%= c.lms %>/js/vendor/ova/catch/css/main.css'
                    ]
                }
            },
            studio: {
                files: {
                    '<%= c.studio %>/css/cms-style-vendor.css': [
                        '<%= c.common %>/css/vendor/normalize.css',
                        '<%= c.bower %>/font-awesome/css/font-awesome.css',
                        '<%= c.common %>/css/vendor/html5-input-polyfills/number-polyfill.css',
                        '<%= c.common %>/js/vendor/CodeMirror/codemirror.css',
                        '<%= c.common %>/css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css',
                        '<%= c.common %>/css/vendor/jquery.qtip.min.css',
                        '<%= c.common %>/js/vendor/markitup/skins/simple/style.css',
                        '<%= c.common %>/js/vendor/markitup/sets/wiki/style.css',
                    ],
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-content.css': [
                        '<%= c.common %>/css/tinymce-studio-content-fonts.css',
                        '<%= c.common %>/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/content.min.css',
                        '<%= c.common %>/css/tinymce-studio-content.css'
                    ],
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-skin.css': [
                        '<%= c.common %>/js/vendor/tinymce/js/tinymce/skins/studio-tmce4/skin.min.css'
                    ],
                    '<%= c.studio %>/css/cms-style-app.css': [
                        '<%= c.studio %>/sass/style-app.css'
                    ],
                    '<%= c.studio %>/css/cms-style-app-rtl.css': [
                        '<%= c.studio %>/sass/style-app-rtl.css'
                    ],
                    '<%= c.studio %>/css/cms-style-app-extend1.css': [
                        '<%= c.studio %>/sass/style-app-extend1.css'
                    ],
                    '<%= c.studio %>/css/cms-style-app-extend1-rtl.css': [
                        '<%= c.studio %>/sass/style-app-extend1-rtl.css'
                    ],
                    '<%= c.studio %>/css/cms-style-xmodule.css': [
                        '<%= c.studio %>/sass/style-xmodule.css'
                    ],
                    '<%= c.studio %>/css/cms-style-xmodule-rtl.css': [
                        '<%= c.studio %>/sass/style-xmodule-rtl.css'
                    ],
                    '<%= c.studio %>/css/cms-style-xmodule-annotations.css': [
                        '<%= c.common %>/css/vendor/ova/annotator.css',
                        '<%= c.common %>/css/vendor/ova/edx-annotator.css',
                        '<%= c.common %>/css/vendor/ova/video-js.min.css',
                        '<%= c.common %>/css/vendor/ova/rangeslider.css',
                        '<%= c.common %>/css/vendor/ova/share-annotator.css',
                        '<%= c.common %>/css/vendor/ova/richText-annotator.css',
                        '<%= c.common %>/css/vendor/ova/tags-annotator.css',
                        '<%= c.common %>/css/vendor/ova/flagging-annotator.css',
                        '<%= c.common %>/css/vendor/ova/diacritic-annotator.css',
                        '<%= c.common %>/css/vendor/ova/grouping-annotator.css',
                        '<%= c.common %>/css/vendor/ova/ova.css',
                        '<%= c.common %>/js/vendor/ova/catch/css/main.css'
                    ]
                }
            }
        },

        cssmin: {
            lms: {
                files: {
                    '<%= c.lms %>/css/lms-style-vendor.css': '<%= c.lms %>/css/lms-style-vendor.css',
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-content.css': '<%= c.lms %>/css/lms-style-vendor-tinymce-content.css',
                    '<%= c.lms %>/css/lms-style-vendor-tinymce-skin.css': '<%= c.lms %>/css/lms-style-vendor-tinymce-skin.css',
                    '<%= c.lms %>/css/lms-style-app.css': '<%= c.lms %>/css/lms-style-app.css',
                    '<%= c.lms %>/css/lms-style-app-extend2.css': '<%= c.lms %>/css/lms-style-app-extend2.css',
                    '<%= c.lms %>/css/lms-style-app-rtl.css': '<%= c.lms %>/css/lms-style-app-rtl.css',
                    '<%= c.lms %>/css/lms-style-app-extend2-rtl.css': '<%= c.lms %>/css/lms-style-app-extend2-rtl.css',
                    '<%= c.lms %>/css/lms-style-course-vendor.css': '<%= c.lms %>/css/lms-style-course-vendor.css',
                    '<%= c.lms %>/css/lms-style-course.css': '<%= c.lms %>/css/lms-style-course.css',
                    '<%= c.lms %>/css/lms-style-course-rtl.css': '<%= c.lms %>/css/lms-style-course-rtl.css',
                    '<%= c.lms %>/css/lms-style-xmodule-annotations.css': '<%= c.lms %>/css/lms-style-xmodule-annotations.css'
                }
            },
            studio: {
                files: {
                    '<%= c.studio %>/css/cms-style-vendor.css': '<%= c.studio %>/css/cms-style-vendor.css',
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-content.css': '<%= c.studio %>/css/cms-style-vendor-tinymce-content.css',
                    '<%= c.studio %>/css/cms-style-vendor-tinymce-skin.css': '<%= c.studio %>/css/cms-style-vendor-tinymce-skin.css',
                    '<%= c.studio %>/css/cms-style-app.css': '<%= c.studio %>/css/cms-style-app.css',
                    '<%= c.studio %>/css/cms-style-app-rtl.css': '<%= c.studio %>/css/cms-style-app-rtl.css',
                    '<%= c.studio %>/css/cms-style-app-extend1.css': '<%= c.studio %>/css/cms-style-app-extend1.css',
                    '<%= c.studio %>/css/cms-style-app-extend1-rtl.css': '<%= c.studio %>/css/cms-style-app-extend1-rtl.css',
                    '<%= c.studio %>/css/cms-style-xmodule.css': '<%= c.studio %>/css/cms-style-xmodule.css',
                    '<%= c.studio %>/css/cms-style-xmodule-rtl.css': '<%= c.studio %>/css/cms-style-xmodule-rtl.css',
                    '<%= c.studio %>/css/cms-style-xmodule-annotations.css': '<%= c.studio %>/css/cms-style-xmodule-annotations.css'
                }
            }
        },

        coffee: {
            common: {
                expand: true,
                src: [
                    '<%= c.common %>/coffee/**/*.coffee',
                    '<%= c.common %>/xmodule/**/*.coffee'
                ],
                extDot: 'last',
                ext: '.js'
            },
            lms: {
                expand: true,
                src: function () {
                    var paths = [
                        '<%= c.lms %>/coffee/**/*.coffee'
                    ];

                    if (config.theme) {
                        paths.push('<%= c.theme %>/coffee/**/*.coffee');
                    }

                    return paths;
                }(),
                extDot: 'last',
                ext: '.js'
            },

            studio: {
                expand: true,
                src: [
                    '<%= c.studio %>/coffee/**/*.coffee'
                ],
                extDot: 'last',
                ext: '.js'
            }
        },

        concurrent: {
            'watch_lms': {
                options: {
                    logConcurrentOutput: true
                },
                tasks: [
                    'watch:sass_lms',
                    'watch:coffee_common',
                    'watch:coffee_lms'
                ]
            },

            'watch_studio': {
                options: {
                    logConcurrentOutput: true
                },
                tasks: [
                    'watch:sass_studio',
                    'watch:coffee_common',
                    'watch:coffee_studio'
                ]
            },

            'build_lms': {
                tasks: [
                    'lms:css',
                    'lms:js'
                ]
            },

            'build_studio': {
                tasks: [
                    'studio:css',
                    'studio:js'
                ]
            }

        }
    });

    // LMS tasks
    grunt.registerTask('lms', [
        'concurrent:build_lms'
    ]);

    grunt.registerTask('lms:css', [
        'sass:lms',
        'concat:lms'
    ]);

    grunt.registerTask('lms:js', [
        'coffee:common',
        'coffee:lms'
    ]);

    grunt.registerTask('lms:watch', [
        'concurrent:watch_lms'
    ]);

    grunt.registerTask('lms:dev', [
        'lms',
        'lms:watch'
    ]);

    grunt.registerTask('lms:dist', [
        'clean:lms',
        'lms',
        'cssmin:lms'
    ]);


    // Studio tasks
    grunt.registerTask('studio', [
        'concurrent:build_studio'
    ]);

    grunt.registerTask('studio:css', [
        'sass:studio',
        'concat:studio'
    ]);

    grunt.registerTask('studio:js', [
        'coffee:common',
        'coffee:studio'
    ]);

    grunt.registerTask('studio:watch', [
        'concurrent:watch_studio'
    ]);

    grunt.registerTask('studio:dev', [
        'studio',
        'studio:watch'
    ]);

    grunt.registerTask('studio:dist', [
        'clean:studio',
        'studio',
        'cssmin:studio'
    ]);
};
