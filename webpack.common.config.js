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

// These files are used by RequireJS as well, so we can't remove
// the instances of "text!some/file.underscore" (which webpack currently
// processes twice). So instead we have webpack dynamically remove the `text!` prefix
// until we can remove RequireJS from the system.
var filesWithTextBangUnderscore = [
    path.resolve(__dirname, 'cms/static/js/certificates/views/certificate_details.js'),
    path.resolve(__dirname, 'cms/static/js/certificates/views/certificate_editor.js'),
    path.resolve(__dirname, 'cms/static/js/certificates/views/certificate_preview.js'),
    path.resolve(__dirname, 'cms/static/js/certificates/views/signatory_details.js'),
    path.resolve(__dirname, 'cms/static/js/certificates/views/signatory_editor.js'),
    path.resolve(__dirname, 'cms/static/js/views/active_video_upload_list.js'),
    path.resolve(__dirname, 'cms/static/js/views/assets.js'),
    path.resolve(__dirname, 'cms/static/js/views/course_video_settings.js'),
    path.resolve(__dirname, 'cms/static/js/views/edit_chapter.js'),
    path.resolve(__dirname, 'cms/static/js/views/experiment_group_edit.js'),
    path.resolve(__dirname, 'cms/static/js/views/license.js'),
    path.resolve(__dirname, 'cms/static/js/views/modals/move_xblock_modal.js'),
    path.resolve(__dirname, 'cms/static/js/views/move_xblock_breadcrumb.js'),
    path.resolve(__dirname, 'cms/static/js/views/move_xblock_list.js'),
    path.resolve(__dirname, 'cms/static/js/views/paging_header.js'),
    path.resolve(__dirname, 'cms/static/js/views/previous_video_upload_list.js'),
    path.resolve(__dirname, 'cms/static/js/views/previous_video_upload.js'),
    path.resolve(__dirname, 'cms/static/js/views/video_thumbnail.js'),
    path.resolve(__dirname, 'cms/static/js/views/video_transcripts.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/paginated_view.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/paging_footer.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/paging_header.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/progress_circle_view.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/search_field.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/tabbed_view.js'),
    path.resolve(__dirname, 'lms/djangoapps/discussion/static/discussion/js/views/discussion_board_view.js'),
    path.resolve(__dirname, 'lms/djangoapps/discussion/static/discussion/js/views/discussion_fake_breadcrumbs.js'),
    path.resolve(__dirname, 'lms/djangoapps/discussion/static/discussion/js/views/discussion_search_view.js'),
    path.resolve(__dirname, 'lms/djangoapps/discussion/static/discussion/js/views/discussion_user_profile_view.js'),
    path.resolve(__dirname, 'lms/djangoapps/support/static/support/js/views/certificates.js'),
    path.resolve(__dirname, 'lms/djangoapps/support/static/support/js/views/enrollment_modal.js'),
    path.resolve(__dirname, 'lms/djangoapps/support/static/support/js/views/enrollment.js'),
    path.resolve(__dirname, 'lms/djangoapps/support/static/support/js/views/manage_user.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/edit_team_members.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/edit_team.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/instructor_tools.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/team_card.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/team_profile_header_actions.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/team_profile.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/teams_tab.js'),
    path.resolve(__dirname, 'lms/djangoapps/teams/static/teams/js/views/topic_teams.js'),
    path.resolve(__dirname, 'lms/static/js/api_admin/views/catalog_preview.js'),
    path.resolve(__dirname, 'lms/static/js/components/card/views/card.js'),
    path.resolve(__dirname, 'lms/static/js/components/header/views/header.js'),
    path.resolve(__dirname, 'lms/static/js/financial-assistance/views/financial_assistance_form_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/certificate_list_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/certificate_status_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/collection_list_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/course_card_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/course_enroll_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/course_entitlement_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/expired_notification_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/explore_new_programs_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/program_card_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/program_details_sidebar_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/program_details_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/program_header_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/sidebar_view.js'),
    path.resolve(__dirname, 'lms/static/js/learner_dashboard/views/upgrade_message_view.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/account_section_view.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/account_settings_fields.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/account_settings_view.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/FormView.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/LoginView.js'),
    path.resolve(__dirname, 'lms/static/js/student_account/views/RegisterView.js'),
    path.resolve(__dirname, 'lms/static/js/views/fields.js'),
    path.resolve(__dirname, 'lms/static/js/views/image_field.js'),
    path.resolve(__dirname, 'lms/static/js/views/message_banner.js'),
    path.resolve(__dirname, 'openedx/features/course_bookmarks/static/course_bookmarks/js/views/bookmarks_list.js'),
    path.resolve(__dirname, 'openedx/features/course_search/static/course_search/js/spec/course_search_spec.js'),
    path.resolve(
        __dirname,
        'openedx/features/course_search/static/course_search/js/views/course_search_results_view.js'
    ),
    path.resolve(
        __dirname,
        'openedx/features/course_search/static/course_search/js/views/dashboard_search_results_view.js'
    ),
    path.resolve(__dirname, 'openedx/features/course_search/static/course_search/js/views/search_results_view.js'),
    path.resolve(__dirname, 'openedx/features/learner_profile/static/learner_profile/js/views/badge_list_container.js'),
    path.resolve(__dirname, 'openedx/features/learner_profile/static/learner_profile/js/views/badge_list_view.js'),
    path.resolve(__dirname, 'openedx/features/learner_profile/static/learner_profile/js/views/badge_view.js'),
    path.resolve(
        __dirname,
        'openedx/features/learner_profile/static/learner_profile/js/views/learner_profile_fields.js'
    ),
    path.resolve(__dirname, 'openedx/features/learner_profile/static/learner_profile/js/views/section_two_tab.js'),
    path.resolve(__dirname, 'openedx/features/learner_profile/static/learner_profile/js/views/share_modal_view.js')
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
        'js/pages/textbooks': './cms/static/js/pages/textbooks.js',
        NoTextbooks: './cms/static/js/features_jsx/studio/NoTextbooks.jsx',

        // LMS
        SingleSupportForm: './lms/static/support/jsx/single_support_form.jsx',
        AlertStatusBar: './lms/static/js/accessible_components/StatusBarAlert.jsx',
        LearnerAnalyticsDashboard: './lms/static/js/learner_analytics_dashboard/LearnerAnalyticsDashboard.jsx',
        UpsellExperimentModal: './lms/static/common/js/components/UpsellExperimentModal.jsx',
        PortfolioExperimentUpsellModal: './lms/static/common/js/components/PortfolioExperimentUpsellModal.jsx',

        // Learner Dashboard
        EntitlementFactory: './lms/static/js/learner_dashboard/course_entitlement_factory.js',
        EntitlementUnenrollmentFactory: './lms/static/js/learner_dashboard/entitlement_unenrollment_factory.js',
        ProgramDetailsFactory: './lms/static/js/learner_dashboard/program_details_factory.js',
        ProgramListFactory: './lms/static/js/learner_dashboard/program_list_factory.js',
        UnenrollmentFactory: './lms/static/js/learner_dashboard/unenrollment_factory.js',

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
            'window.jQuery': 'jquery',
            Popper: 'popper.js' // used by bootstrap
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
            // 'backbone': 'backbone',
            'backbone.associations': 'backbone-associations-min',

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
            'common/static/',
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
