(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext',
        'js/discussions_management/views/divided_discussions_inline',
        'js/discussions_management/views/divided_discussions_course_wide',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/models/notification',
        'js/views/notification'
    ],

        function($, _, Backbone, gettext, InlineDiscussionsView, CourseWideDiscussionsView, HtmlUtils) {
            /* global NotificationModel, NotificationView */

            var hiddenClass = 'is-hidden';
            var cohort = 'cohort';
            var none = 'none';
            var enrollmentTrack = 'enrollment_track';

            var DiscussionsView = Backbone.View.extend({
                events: {
                    'click .division-scheme': 'divisionSchemeChanged'
                },

                initialize: function(options) {
                    this.template = HtmlUtils.template($('#discussions-tpl').text());
                    this.context = options.context;
                    this.discussionSettings = options.discussionSettings;
                },

                render: function() {
                    var selectedScheme, topicNav;
                    HtmlUtils.setHtml(this.$el, this.template({
                        availableSchemes: this.getDivisionSchemeData(this.discussionSettings.attributes.division_scheme)
                    }));
                    selectedScheme = this.getSelectedScheme();
                    topicNav = this.getTopicNav();
                    this.hideTopicNav(selectedScheme, topicNav);
                    this.showDiscussionTopics();
                    return this;
                },

                getDivisionSchemeData: function(selectedScheme) {
                    var self = this;
                    return [
                        {
                            key: none,
                            displayName: gettext('Not divided'),
                            descriptiveText: gettext('Discussions are unified; all learners interact with posts from other learners, regardless of the group they are in.'), //  eslint-disable-line max-len
                            selected: selectedScheme === none,
                            enabled: true // always leave none enabled
                        },
                        {
                            key: enrollmentTrack,
                            displayName: gettext('Enrollment Tracks'),
                            descriptiveText: gettext('Use enrollment tracks as the basis for dividing discussions. All learners, regardless of their enrollment track, see the same discussion topics, but within divided topics, only learners who are in the same enrollment track see and respond to each others’ posts.'), //  eslint-disable-line max-len
                            selected: selectedScheme === enrollmentTrack,
                            enabled: self.isSchemeAvailable(enrollmentTrack) || selectedScheme === enrollmentTrack
                        },
                        {
                            key: cohort,
                            displayName: gettext('Cohorts'),
                            descriptiveText: gettext('Use cohorts as the basis for dividing discussions. All learners, regardless of cohort, see the same discussion topics, but within divided topics, only members of the same cohort see and respond to each others’ posts. '), //  eslint-disable-line max-len
                            selected: selectedScheme === cohort,
                            enabled: self.isSchemeAvailable(cohort) || selectedScheme === cohort
                        }

                    ];
                },

                isSchemeAvailable: function(scheme) {
                    var self = this;
                    return self.discussionSettings.attributes.available_division_schemes.indexOf(scheme) !== -1;
                },

                showMessage: function(message, type) {
                    var self = this,
                        model = new NotificationModel({type: type || 'confirmation', title: message});
                    this.removeNotification();
                    this.notification = new NotificationView({
                        model: model
                    });
                    self.$('.division-scheme-container').prepend(this.notification.$el);
                    this.notification.render();
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
                        messageSpan = this.$('.division-scheme-message'),
                        fieldData = {
                            division_scheme: selectedScheme
                        };

                    this.hideTopicNav(selectedScheme, topicNav);
                    this.saveDivisionScheme(topicNav, fieldData);
                    this.showSelectMessage(selectedScheme, messageSpan);
                },

                saveDivisionScheme: function($element, fieldData) {
                    var self = this,
                        discussionSettingsModel = this.discussionSettings,
                        saveOperation = $.Deferred(),
                        showErrorMessage;

                    this.removeNotification();
                    showErrorMessage = function(message) {
                        self.showMessage(message, 'error');
                    };

                    discussionSettingsModel.save(
                        fieldData, {patch: true, wait: true}
                    ).done(function() {
                        saveOperation.resolve();
                        self.showMessage(
                            gettext('Your changes have been saved.')
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
                            errorMessage = gettext('We\'ve encountered an error. ' +
                                'Refresh your browser and then try again.');
                        }
                        showErrorMessage(errorMessage);
                        saveOperation.reject();
                    });
                },

                hideTopicNav: function(selectedScheme, topicNav) {
                    if (selectedScheme === none) {
                        topicNav.addClass(hiddenClass);
                    } else {
                        topicNav.removeClass(hiddenClass);
                    }
                },

                showSelectMessage: function(selectedScheme, messageSpan) {
                    switch (selectedScheme) {
                    case none:
                        messageSpan.text(gettext('Discussion topics in the course are not divided.'));
                        break;
                    case enrollmentTrack:
                        messageSpan.text(gettext('Any divided discussion topics are divided based on enrollment track.')); //  eslint-disable-line max-len
                        break;
                    case cohort:
                        messageSpan.text(gettext('Any divided discussion topics are divided based on cohort.'));
                        break;
                    default:
                        break;
                    }
                },

                getSectionCss: function(section) {
                    return ".instructor-nav .nav-item [data-section='" + section + "']";
                },

                showDiscussionTopics: function() {
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
