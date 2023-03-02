(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext',
        'js/discussions_management/views/divided_discussions_inline',
        'js/discussions_management/views/divided_discussions_course_wide',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils',
        'js/views/base_dashboard_view',
        'js/models/notification',
        'js/views/notification'
    ],

    function($, _, Backbone, gettext, InlineDiscussionsView,
        CourseWideDiscussionsView,
        HtmlUtils, StringUtils, BaseDashboardView) {
        /* global NotificationModel, NotificationView */

        var HIDDEN_CLASS = 'hidden';
        var TWO_COLUMN_CLASS = 'two-column-layout';
        var THREE_COLUMN_CLASS = 'three-column-layout';
        var COHORT = 'cohort';
        var NONE = 'none';
        var ENROLLMENT_TRACK = 'enrollment_track';

        var DiscussionsView = BaseDashboardView.extend({
            events: {
                'click .division-scheme': 'divisionSchemeChanged',
                'change .cohorts-state': 'onCohortsEnabledChanged'
            },

            initialize: function(options) {
                this.template = HtmlUtils.template($('#discussions-tpl').text());
                this.context = options.context;
                this.discussionSettings = options.discussionSettings;
                this.listenTo(this.pubSub, 'cohorts:state', this.cohortStateUpdate, this);
            },

            render: function() {
                var numberAvailableSchemes = this.discussionSettings.attributes.available_division_schemes.length;

                HtmlUtils.setHtml(this.$el, this.template({
                    availableSchemes: this.getDivisionSchemeData(this.discussionSettings.attributes.division_scheme), //  eslint-disable-line max-len
                    layoutClass: numberAvailableSchemes === 2 ? THREE_COLUMN_CLASS : TWO_COLUMN_CLASS
                }));
                this.updateTopicVisibility(this.getSelectedScheme(), this.getTopicNav());
                this.renderTopics();

                if (this.isSchemeAvailable(COHORT) ||
                        (!this.isSchemeAvailable(COHORT) && this.getSelectedScheme() === COHORT)) {
                    this.showCohortSchemeControl(true);
                }
                return this;
            },

            getDivisionSchemeData: function(selectedScheme) {
                return [
                    {
                        key: NONE,
                        displayName: gettext('Not divided'),
                        descriptiveText: gettext('Discussions are unified; all learners interact with posts from other learners, regardless of the group they are in.'), //  eslint-disable-line max-len
                        selected: selectedScheme === NONE,
                        enabled: true // always leave none enabled
                    },
                    {
                        key: ENROLLMENT_TRACK,
                        displayName: gettext('Enrollment Tracks'),
                        descriptiveText: gettext('Use enrollment tracks as the basis for dividing discussions. All learners, regardless of their enrollment track, see the same discussion topics, but within divided topics, only learners who are in the same enrollment track see and respond to each others’ posts.'), //  eslint-disable-line max-len
                        selected: selectedScheme === ENROLLMENT_TRACK,
                        enabled: this.isSchemeAvailable(ENROLLMENT_TRACK) || selectedScheme === ENROLLMENT_TRACK
                    },
                    {
                        key: COHORT,
                        displayName: gettext('Cohorts'),
                        descriptiveText: gettext('Use cohorts as the basis for dividing discussions. All learners, regardless of cohort, see the same discussion topics, but within divided topics, only members of the same cohort see and respond to each others’ posts. '), //  eslint-disable-line max-len
                        selected: selectedScheme === COHORT,
                        enabled: this.isSchemeAvailable(COHORT) || selectedScheme === COHORT
                    }

                ];
            },

            isSchemeAvailable: function(scheme) {
                return this.discussionSettings.attributes.available_division_schemes.indexOf(scheme) !== -1;
            },

            showMessage: function(message, type) {
                var model = new NotificationModel({type: type || 'confirmation', title: message});
                this.removeNotification();
                this.notification = new NotificationView({
                    model: model
                });
                this.$('.division-scheme-container').prepend(this.notification.$el);
                this.notification.render();
            },

            cohortStateUpdate: function(state) {
                var cohortIndex;
                if (state.is_cohorted && !this.isSchemeAvailable(COHORT)) {
                    this.discussionSettings.attributes.available_division_schemes.push(COHORT);
                } else if (!state.is_cohorted && this.getSelectedScheme() !== COHORT) {
                    cohortIndex = this.discussionSettings.attributes.available_division_schemes.indexOf(COHORT);
                    if (cohortIndex > -1) {
                        this.discussionSettings.attributes.available_division_schemes.splice(cohortIndex, 1);
                    }
                }

                if (!this.isSchemeAvailable(ENROLLMENT_TRACK)) {
                    this.showDiscussionManagement(state.is_cohorted);
                }
                if (this.getSelectedScheme() !== COHORT) {
                    this.showCohortSchemeControl(state.is_cohorted);
                }
            },

            showDiscussionManagement: function(show) {
                if (!show) {
                    $('.btn-link.discussions_management').addClass(HIDDEN_CLASS);
                    $('#discussions_management').addClass(HIDDEN_CLASS);
                } else {
                    $('.btn-link.discussions_management').removeClass(HIDDEN_CLASS);
                    $('#discussions_management').removeClass(HIDDEN_CLASS);
                }
            },

            showCohortSchemeControl: function(show) {
                if (!show) {
                    $('.division-scheme-item.cohort').addClass(HIDDEN_CLASS);
                    // Since we are removing the cohort scheme, we can have at most 2 columns.
                    $('.division-scheme-item').removeClass(THREE_COLUMN_CLASS).addClass(TWO_COLUMN_CLASS);
                } else {
                    $('.division-scheme-item.cohort').removeClass(HIDDEN_CLASS);
                    if (this.isSchemeAvailable(ENROLLMENT_TRACK)) {
                        $('.division-scheme-item').removeClass(TWO_COLUMN_CLASS).addClass(THREE_COLUMN_CLASS);
                    } else {
                        $('.division-scheme-item').removeClass(THREE_COLUMN_CLASS).addClass(TWO_COLUMN_CLASS);
                    }
                }
            },

            removeNotification: function() {
                if (this.notification) {
                    this.notification.remove();
                }
            },

            getSelectedScheme: function() {
                return this.$('input[name="division-scheme"]:checked').val();
            },

            getTopicNav: function() {
                return this.$('.topic-division-nav');
            },

            divisionSchemeChanged: function() {
                var selectedScheme = this.getSelectedScheme(),
                    topicNav = this.getTopicNav(),
                    fieldData = {
                        division_scheme: selectedScheme
                    };

                this.updateTopicVisibility(selectedScheme, topicNav);
                this.saveDivisionScheme(topicNav, fieldData, selectedScheme);
            },

            saveDivisionScheme: function($element, fieldData, selectedScheme) {
                var self = this,
                    discussionSettingsModel = this.discussionSettings,
                    showErrorMessage,
                    details = '';

                this.removeNotification();
                showErrorMessage = function(message) {
                    self.showMessage(message, 'error');
                };

                discussionSettingsModel.save(
                    fieldData, {patch: true, wait: true}
                ).done(function() {
                    switch (selectedScheme) {
                    case NONE:
                        details = gettext('Discussion topics in the course are not divided.');
                        break;
                    case ENROLLMENT_TRACK:
                        details = gettext('Any divided discussion topics are divided based on enrollment track.'); //  eslint-disable-line max-len
                        break;
                    case COHORT:
                        details = gettext('Any divided discussion topics are divided based on cohort.');
                        break;
                    default:
                        break;
                    }
                    self.showMessage(
                        StringUtils.interpolate(
                            gettext('Your changes have been saved. {details}'),
                            {details: details},
                            true
                        )
                    );
                }).fail(function(result) {
                    var errorMessage = null,
                        jsonResponse;
                    try {
                        jsonResponse = JSON.parse(result.responseText);
                        errorMessage = jsonResponse.error;
                    } catch (e) {
                        // Ignore the exception and show the default error message instead.
                    }
                    if (!errorMessage) {
                        errorMessage = gettext('We have encountered an error. Refresh your browser and then try again.'); //  eslint-disable-line max-len
                    }
                    showErrorMessage(errorMessage);
                });
            },

            updateTopicVisibility: function(selectedScheme, topicNav) {
                if (selectedScheme === NONE) {
                    topicNav.addClass(HIDDEN_CLASS);
                } else {
                    topicNav.removeClass(HIDDEN_CLASS);
                }
            },

            getSectionCss: function(section) {
                return ".instructor-nav .nav-item [data-section='" + section + "']";
            },

            renderTopics: function() {
                var dividedDiscussionsElement = this.$('.discussions-nav');
                if (!this.CourseWideDiscussionsView) {
                    this.CourseWideDiscussionsView = new CourseWideDiscussionsView({
                        el: dividedDiscussionsElement,
                        model: this.context.courseDiscussionTopicDetailsModel,
                        discussionSettings: this.discussionSettings
                    }).render();
                }

                if (!this.InlineDiscussionsView) {
                    this.InlineDiscussionsView = new InlineDiscussionsView({
                        el: dividedDiscussionsElement,
                        model: this.context.courseDiscussionTopicDetailsModel,
                        discussionSettings: this.discussionSettings
                    }).render();
                }
            }
        });
        return DiscussionsView;
    });
}).call(this, define || RequireJS.define);
