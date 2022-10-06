/* eslint-env node */

'use strict';

var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var StringReplace = require('string-replace-webpack-plugin');
var Merge = require('webpack-merge');

var files = require('./webpack-config/file-lists.js');
var xmoduleJS = require('./common/static/xmodule/webpack.xmodule.config.js');

var filesWithRequireJSBlocks = [
    path.resolve(__dirname, 'common/static/common/js/components/utils/view_utils.js'),
    /descriptors\/js/,
    /modules\/js/,
    /xmodule\/js\/src\//
];

var defineHeader = /\(function ?\(((define|require|requirejs|\$)(, )?)+\) ?\{/;
var defineCallFooter = /\}\)\.call\(this, ((define|require)( \|\| RequireJS\.(define|require))?(, )?)+?\);/;
var defineDirectFooter = /\}\(((window\.)?(RequireJS\.)?(requirejs|define|require|jQuery)(, )?)+\)\);/;
var defineFancyFooter = /\}\).call\(\s*this(\s|.)*define(\s|.)*\);/;
var defineFooter = new RegExp('(' + defineCallFooter.source + ')|('
                             + defineDirectFooter.source + ')|('
                             + defineFancyFooter.source + ')', 'm');

var workerConfig = function() {
    try {
        return {
            webworker: {
                target: 'webworker',
                context: __dirname,
                entry: require('../workers.json'),
                output: {
                    filename: '[name].js',
                    path: path.resolve(__dirname, 'common/static/bundles')
                },
                plugins: [
                    new BundleTracker({
                        path: process.env.STATIC_ROOT_LMS,
                        filename: 'webpack-worker-stats.json'
                    })
                ],
                module: {
                    rules: [
                        {
                            test: /\.(js|jsx)$/,
                            include: [
                                /node_modules\//
                            ],
                            use: 'babel-loader'
                        }
                    ]
                },
                resolve: {
                    extensions: ['.js']
                }
            }
        };
    } catch (err) {
        return null;
    }
};

module.exports = Merge.smart({
    web: {
        context: __dirname,

        entry: {
            // Studio
            Import: './cms/static/js/features/import/factories/import.js',
            CourseOrLibraryListing: './cms/static/js/features_jsx/studio/CourseOrLibraryListing.jsx',
            LibrarySourcedBlockPicker: './xmodule/assets/library_source_block/LibrarySourcedBlockPicker.jsx',  // eslint-disable-line max-len
            'js/factories/textbooks': './cms/static/js/factories/textbooks.js',
            'js/factories/container': './cms/static/js/factories/container.js',
            'js/factories/context_course': './cms/static/js/factories/context_course.js',
            'js/factories/library': './cms/static/js/factories/library.js',
            'js/factories/xblock_validation': './cms/static/js/factories/xblock_validation.js',
            'js/factories/edit_tabs': './cms/static/js/factories/edit_tabs.js',
            'js/sock': './cms/static/js/sock.js',

            // LMS
            SingleSupportForm: './lms/static/support/jsx/single_support_form.jsx',
            AlertStatusBar: './lms/static/js/accessible_components/StatusBarAlert.jsx',
            EntitlementSupportPage: './lms/djangoapps/support/static/support/jsx/entitlements/index.jsx',
            LinkProgramEnrollmentsSupportPage: './lms/djangoapps/support/static/support/jsx/' +
                                               'program_enrollments/index.jsx',
            ProgramEnrollmentsInspectorPage: './lms/djangoapps/support/static/support/jsx/' +
                                               'program_enrollments/inspector.jsx',
            PasswordResetConfirmation: './lms/static/js/student_account/components/PasswordResetConfirmation.jsx',
            StudentAccountDeletion: './lms/static/js/student_account/components/StudentAccountDeletion.jsx',
            StudentAccountDeletionInitializer: './lms/static/js/student_account/StudentAccountDeletionInitializer.js',
            ProblemBrowser: './lms/djangoapps/instructor/static/instructor/ProblemBrowser/index.jsx',
            DemographicsCollectionBanner: './lms/static/js/demographics_collection/DemographicsCollectionBanner.jsx',
            DemographicsCollectionModal: './lms/static/js/demographics_collection/DemographicsCollectionModal.jsx',
            AxiosJwtTokenService: './lms/static/js/jwt_auth/AxiosJwtTokenService.js',
            EnterpriseLearnerPortalModal: './lms/static/js/learner_dashboard/EnterpriseLearnerPortalModal.jsx',
            RecommendationsPanel: './lms/static/js/learner_dashboard/RecommendationsPanel.jsx',
            Static2UCallouts: './lms/static/js/learner_dashboard/Static2UCallouts.jsx',

            // Learner Dashboard
            EntitlementFactory: './lms/static/js/learner_dashboard/course_entitlement_factory.js',
            EntitlementUnenrollmentFactory: './lms/static/js/learner_dashboard/entitlement_unenrollment_factory.js',
            ProgramDetailsFactory: './lms/static/js/learner_dashboard/program_details_factory.js',
            ProgramListFactory: './lms/static/js/learner_dashboard/program_list_factory.js',
            UnenrollmentFactory: './lms/static/js/learner_dashboard/unenrollment_factory.js',
            CompletionOnViewService: './lms/static/completion/js/CompletionOnViewService.js',

            // Features
            CourseSock: './openedx/features/course_experience/static/course_experience/js/CourseSock.js',
            Currency: './openedx/features/course_experience/static/course_experience/js/currency.js',

            AnnouncementsView: './openedx/features/announcements/static/announcements/jsx/Announcements.jsx',
            CookiePolicyBanner: './common/static/js/src/CookiePolicyBanner.jsx',

            // Common
            ReactRenderer: './common/static/js/src/ReactRenderer.jsx',
            XModuleShim: './xmodule/js/src/xmodule.js',
            VerticalStudentView: './xmodule/assets/vertical/public/js/vertical_student_view.js',
            commons: 'babel-polyfill'
        },

        output: {
            path: path.resolve(__dirname, 'common/static/bundles'),
            libraryTarget: 'window'
        },

        plugins: [
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.NamedModulesPlugin(),
            new BundleTracker({
                path: process.env.STATIC_ROOT_CMS,
                filename: 'webpack-stats.json'
            }),
            new BundleTracker({
                path: process.env.STATIC_ROOT_LMS,
                filename: 'webpack-stats.json'
            }),
            new webpack.ProvidePlugin({
                _: 'underscore',
                $: 'jquery',
                jQuery: 'jquery',
                'window.jQuery': 'jquery',
                Popper: 'popper.js', // used by bootstrap
                CodeMirror: 'codemirror',
                'edx.HtmlUtils': 'edx-ui-toolkit/js/utils/html-utils',
                AjaxPrefix: 'ajax_prefix',
                // This is used by some XModules/XBlocks, which don't have
                // any other way to declare that dependency.
                $script: 'scriptjs'
            }),

            // Note: Until karma-webpack releases v3, it doesn't play well with
            // the CommonsChunkPlugin. We have a kludge in karma.common.conf.js
            // that dynamically removes this plugin from webpack config when
            // running those tests (the details are in that file). This is a
            // recommended workaround, as this plugin is just an optimization. But
            // because of this, we really don't want to get too fancy with how we
            // invoke this plugin until we can upgrade karma-webpack.
            new webpack.optimize.CommonsChunkPlugin({
                // If the value below changes, update the render_bundle call in
                // common/djangoapps/pipeline_mako/templates/static_content.html
                name: 'commons',
                filename: 'commons.js',
                minChunks: 10
            })
        ],

        module: {
            noParse: [
                // See sinon/webpack interaction weirdness:
                // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
                // (I've tried every other suggestion solution on that page, this
                // was the only one that worked.)
                /\/sinon\.js|codemirror-compressed\.js|hls\.js|tinymce.js/
            ],
            rules: [
                {
                    test: files.namespacedRequire.concat(files.textBangUnderscore, filesWithRequireJSBlocks),
                    loader: StringReplace.replace(
                        ['babel-loader'],
                        {
                            replacements: [
                                {
                                    pattern: defineHeader,
                                    replacement: function() { return ''; }
                                },
                                {
                                    pattern: defineFooter,
                                    replacement: function() { return ''; }
                                },
                                {
                                    pattern: /(\/\* RequireJS) \*\//g,
                                    replacement: function(match, p1) { return p1; }
                                },
                                {
                                    pattern: /\/\* Webpack/g,
                                    replacement: function(match) { return match + ' */'; }
                                },
                                {
                                    pattern: /text!(.*?\.underscore)/g,
                                    replacement: function(match, p1) { return p1; }
                                },
                                {
                                    pattern: /RequireJS.require/g,
                                    replacement: function() {
                                        return 'require';
                                    }
                                }
                            ]
                        }
                    )
                },
                {
                    test: /\.(js|jsx)$/,
                    exclude: [
                        /node_modules/,
                        files.namespacedRequire,
                        files.textBangUnderscore,
                        filesWithRequireJSBlocks
                    ],
                    use: 'babel-loader'
                },
                {
                    test: /\.(js|jsx)$/,
                    include: [
                        /paragon/
                    ],
                    use: 'babel-loader'
                },
                {
                    test: path.resolve(__dirname, 'common/static/js/src/ajax_prefix.js'),
                    use: [
                        'babel-loader',
                        {
                            loader: 'exports-loader',
                            options: {
                                'this.AjaxPrefix': true
                            }
                        }
                    ]
                },
                {
                    test: /\.underscore$/,
                    use: 'raw-loader'
                },
                {
                    // This file is used by both RequireJS and Webpack and depends on window globals
                    // This is a dirty hack and shouldn't be replicated for other files.
                    test: path.resolve(__dirname, 'cms/static/cms/js/main.js'),
                    loader: StringReplace.replace(
                        ['babel-loader'],
                        {
                            replacements: [
                                {
                                    pattern: /\(function\(AjaxPrefix\) {/,
                                    replacement: function() { return ''; }
                                },
                                {
                                    pattern: /], function\(domReady, \$, str, Backbone, gettext, NotificationView\) {/,
                                    replacement: function() {
                                        // eslint-disable-next-line
                                        return '], function(domReady, $, str, Backbone, gettext, NotificationView, AjaxPrefix) {';
                                    }
                                },
                                {
                                    pattern: /'..\/..\/common\/js\/components\/views\/feedback_notification',/,
                                    replacement: function() {
                                        return "'../../common/js/components/views/feedback_notification'," +
                                               "'AjaxPrefix',";
                                    }
                                },
                                {
                                    pattern: /}\).call\(this, AjaxPrefix\);/,
                                    replacement: function() { return ''; }
                                },
                                {
                                    pattern: /'..\/..\/common\/js\/components\/views\/feedback_notification',/,
                                    replacement: function() {
                                        return "'../../common/js/components/views/feedback_notification'," +
                                               "'AjaxPrefix',";
                                    }
                                }
                            ]
                        }
                    )
                },
                {
                    test: /\.(woff2?|ttf|eot)(\?v=\d+\.\d+\.\d+)?$/,
                    loader: 'file-loader'
                },
                {
                    test: /\.svg$/,
                    loader: 'svg-inline-loader'
                },
                {
                    test: /xblock\/core/,
                    loader: 'exports-loader?window.XBlock!' +
                            'imports-loader?jquery,jquery.immediateDescendents,this=>window'
                },
                {
                    test: /xblock\/runtime.v1/,
                    loader: 'exports-loader?window.XBlock!imports-loader?XBlock=xblock/core,this=>window'
                },
                {
                    test: /descriptors\/js/,
                    loader: 'imports-loader?this=>window'
                },
                {
                    test: /modules\/js/,
                    loader: 'imports-loader?this=>window'
                },
                {
                    test: /codemirror/,
                    loader: 'exports-loader?window.CodeMirror'
                },
                {
                    test: /tinymce/,
                    loader: 'imports-loader?this=>window'
                },
                {
                    test: /xmodule\/js\/src\/xmodule/,
                    loader: 'exports-loader?window.XModule!imports-loader?this=>window'
                },
                {
                    test: /mock-ajax/,
                    loader: 'imports-loader?exports=>false'
                },
                {
                    test: /d3.min/,
                    use: [
                        'babel-loader',
                        {
                            loader: 'exports-loader',
                            options: {
                                d3: true
                            }
                        }
                    ]
                },
                {
                    test: /logger/,
                    loader: 'imports-loader?this=>window'
                },
                {
                    test: /\.css$/,
                    use: [
                        'style-loader',
                        {
                            loader: 'css-loader',
                            options: {
                                modules: true
                            }
                        }
                    ]
                }
            ]
        },

        resolve: {
            extensions: ['.js', '.jsx', '.json'],
            alias: {
                AjaxPrefix: 'ajax_prefix',
                accessibility: 'accessibility_tools',
                codemirror: 'codemirror-compressed',
                datepair: 'timepicker/datepair',
                'edx-ui-toolkit': 'edx-ui-toolkit/src/',  // @TODO: some paths in toolkit are not valid relative paths
                ieshim: 'ie_shim',
                jquery: 'jquery/src/jquery',  // Use the non-diqst form of jQuery for better debugging + optimization
                'jquery.flot': 'flot/jquery.flot.min',
                'jquery.ui': 'jquery-ui.min',
                'jquery.tinymce': 'jquery.tinymce.min',
                'jquery.inputnumber': 'html5-input-polyfills/number-polyfill',
                'jquery.qtip': 'jquery.qtip.min',
                'jquery.smoothScroll': 'jquery.smooth-scroll.min',
                'jquery.timepicker': 'timepicker/jquery.timepicker',
                'backbone.associations': 'backbone-associations/backbone-associations-min',
                squire: 'Squire',
                tinymce: 'tinymce',

                // See sinon/webpack interaction weirdness:
                // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
                // (I've tried every other suggestion solution on that page, this
                // was the only one that worked.)
                sinon: __dirname + '/node_modules/sinon/pkg/sinon.js',
                hls: 'hls.js/dist/hls.js'
            },
            modules: [
                'cms/djangoapps/pipeline_js/js',
                'cms/static',
                'cms/static/cms/js',
                'cms/templates/js',
                'lms/static',
                path.resolve(__dirname),
                'xmodule/js/src',
                'xmodule/assets/word_cloud/src/js',
                'common/static',
                'common/static/coffee/src',
                'common/static/common/js',
                'common/static/common/js/vendor/',
                'common/static/common/js/components',
                'common/static/js/src',
                'common/static/js/vendor/',
                'common/static/js/vendor/jQuery-File-Upload/js/',
                'common/static/js/vendor/tinymce/js/tinymce',
                'node_modules',
                'common/static/xmodule'
            ]
        },

        resolveLoader: {
            alias: {
                text: 'raw-loader'  // Compatibility with RequireJSText's text! loader, uses raw-loader under the hood
            }
        },

        externals: {
            $: 'jQuery',
            backbone: 'Backbone',
            canvas: 'canvas',
            gettext: 'gettext',
            jquery: 'jQuery',
            logger: 'Logger',
            underscore: '_',
            URI: 'URI',
            XBlockToXModuleShim: 'XBlockToXModuleShim',
            XModule: 'XModule'
        },

        watchOptions: {
            poll: true
        },

        node: {
            fs: 'empty'
        }

    }
}, {web: xmoduleJS}, workerConfig());
