/* eslint-env node */

'use strict';

var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var StringReplace = require('string-replace-webpack-plugin');

var namespacedRequireFiles = [
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback_notification.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback_prompt.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback.js'),
    path.resolve(__dirname, 'common/static/common/js/components/utils/view_utils.js')
];

var defineHeader = /\(function ?\(define(, require)?\) ?\{/;
var defineFooter = /\}\)\.call\(this, define \|\| RequireJS\.define(, require \|\| RequireJS\.require)?\);/;

module.exports = {
    context: __dirname,

    entry: {
        // Studio
        Import: './cms/static/js/features/import/factories/import.js',
        CourseOrLibraryListing: './cms/static/js/features_jsx/studio/CourseOrLibraryListing.jsx',
        'js/pages/login': './cms/static/js/pages/login.js',

        // LMS
        SingleSupportForm: './lms/static/support/jsx/single_support_form.jsx',
        AlertStatusBar: './lms/static/js/accessible_components/StatusBarAlert.jsx',
        LearnerAnalyticsDashboard: './lms/static/js/learner_analytics_dashboard/LearnerAnalyticsDashboard.jsx',
        UpsellExperimentModal: './lms/static/common/js/components/UpsellExperimentModal.jsx',
        PortfolioExperimentUpsellModal: './lms/static/common/js/components/PortfolioExperimentUpsellModal.jsx',

        // Features
        CourseGoals: './openedx/features/course_experience/static/course_experience/js/CourseGoals.js',
        CourseHome: './openedx/features/course_experience/static/course_experience/js/CourseHome.js',
        CourseOutline: './openedx/features/course_experience/static/course_experience/js/CourseOutline.js',
        CourseSock: './openedx/features/course_experience/static/course_experience/js/CourseSock.js',
        CourseTalkReviews: './openedx/features/course_experience/static/course_experience/js/CourseTalkReviews.js',
        Currency: './openedx/features/course_experience/static/course_experience/js/currency.js',
        Enrollment: './openedx/features/course_experience/static/course_experience/js/Enrollment.js',
        LatestUpdate: './openedx/features/course_experience/static/course_experience/js/LatestUpdate.js',
        WelcomeMessage: './openedx/features/course_experience/static/course_experience/js/WelcomeMessage.js',

        // Common
        ReactRenderer: './common/static/js/src/ReactRenderer.jsx'
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
            'window.jQuery': 'jquery'
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
            minChunks: 3
        })
    ],

    module: {
        noParse: [
            // See sinon/webpack interaction weirdness:
            // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
            // (I've tried every other suggestion solution on that page, this
            // was the only one that worked.)
            /\/sinon\.js/
        ],
        rules: [
            {
                test: namespacedRequireFiles,
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
                            }
                        ]
                    }
                )
            },
            {
                test: /\.(js|jsx)$/,
                exclude: [
                    /node_modules/,
                    namespacedRequireFiles
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
                test: /\.coffee$/,
                exclude: /node_modules/,
                use: 'coffee-loader'
            },
            {
                test: /\.underscore$/,
                use: 'raw-loader'
            },
            {
                // This file is used by both RequireJS and Webpack and depends on window globals
                // This is a dirty hack and shouldn't be replicated for other files.
                test: path.resolve(__dirname, 'cms/static/cms/js/main.js'),
                use: {
                    loader: 'imports-loader',
                    options: {
                        AjaxPrefix:
                            'exports-loader?this.AjaxPrefix!../../../../common/static/coffee/src/ajax_prefix.coffee'
                    }
                }
            },
            {
                test: /\.(woff2?|ttf|svg|eot)(\?v=\d+\.\d+\.\d+)?$/,
                loader: 'file-loader'
            }
        ]
    },

    resolve: {
        extensions: ['.js', '.jsx', '.json', '.coffee'],
        alias: {
            'edx-ui-toolkit': 'edx-ui-toolkit/src/',  // @TODO: some paths in toolkit are not valid relative paths
            'jquery.ui': 'jQuery-File-Upload/js/vendor/jquery.ui.widget.js',
            jquery: 'jquery/src/jquery',  // Use the non-dist form of jQuery for better debugging + optimization

            // See sinon/webpack interaction weirdness:
            // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
            // (I've tried every other suggestion solution on that page, this
            // was the only one that worked.)
            sinon: __dirname + '/node_modules/sinon/pkg/sinon.js'
        },
        modules: [
            'node_modules',
            'common/static/js/vendor/',
            'cms/static',
            'common/static/js/src'
        ]
    },

    resolveLoader: {
        alias: {
            text: 'raw-loader'  // Compatibility with RequireJSText's text! loader, uses raw-loader under the hood
        }
    },

    externals: {
        backbone: 'Backbone',
        coursetalk: 'CourseTalk',
        gettext: 'gettext',
        jquery: 'jQuery',
        logger: 'Logger',
        underscore: '_',
        URI: 'URI'
    },

    watchOptions: {
        poll: true
    }
};
