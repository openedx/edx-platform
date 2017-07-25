(function(define) {
    'use strict';

    define(
        [
            'gettext', 'jquery', 'underscore', 'backbone', 'edx-ui-toolkit/js/utils/html-utils',
            'common/js/components/views/tabbed_view',
            'learner_profile/js/views/section_two_tab',
            'text!learner_profile/templates/learner_profile.underscore',
            'edx-ui-toolkit/js/utils/string-utils'
        ],
        function(gettext, $, _, Backbone, HtmlUtils, TabbedView, SectionTwoTab, learnerProfileTemplate, StringUtils) {
            var LearnerProfileView = Backbone.View.extend({

                initialize: function(options) {
                    var Router;
                    this.options = _.extend({}, options);
                    _.bindAll(this, 'showFullProfile', 'render', 'renderFields', 'showLoadingError');
                    this.listenTo(this.options.preferencesModel, 'change:account_privacy', this.render);
                    Router = Backbone.Router.extend({
                        routes: {':about_me': 'loadTab', ':accomplishments': 'loadTab'}
                    });

                    this.router = new Router();
                    this.firstRender = true;
                },

                template: _.template(learnerProfileTemplate),

                showFullProfile: function() {
                    var isAboveMinimumAge = this.options.accountSettingsModel.isAboveMinimumAge();
                    if (this.options.ownProfile) {
                        return isAboveMinimumAge
                            && this.options.preferencesModel.get('account_privacy') === 'all_users';
                    } else {
                        return this.options.accountSettingsModel.get('profile_is_public');
                    }
                },

                setActiveTab: function(tab) {
                    // This tab may not actually exist.
                    if (this.tabbedView.getTabMeta(tab).tab) {
                        this.tabbedView.setActiveTab(tab);
                    }
                },

                render: function() {
                    var tabs,
                        self = this;

                    this.sectionTwoView = new SectionTwoTab({
                        viewList: this.options.sectionTwoFieldViews,
                        showFullProfile: this.showFullProfile,
                        ownProfile: this.options.ownProfile
                    });


                    HtmlUtils.setHtml(this.$el, HtmlUtils.template(learnerProfileTemplate)({
                        username: self.options.accountSettingsModel.get('username'),
                        name: self.options.accountSettingsModel.get('name'),
                        ownProfile: self.options.ownProfile,
                        showFullProfile: self.showFullProfile(),
                        profile_header: gettext('My Profile'),
                        profile_subheader:
                            StringUtils.interpolate(
                                gettext('Build out your profile to personalize your identity on {platform_name}.'), {
                                    platform_name: self.options.platformName
                                }
                            )
                    }));
                    this.renderFields();

                    if (this.showFullProfile() && (this.options.accountSettingsModel.get('accomplishments_shared'))) {
                        tabs = [
                            {view: this.sectionTwoView, title: gettext('About Me'), url: 'about_me'},
                            {
                                view: this.options.badgeListContainer,
                                title: gettext('Accomplishments'),
                                url: 'accomplishments'
                            }
                        ];

                        // Build the accomplishments Tab and fill with data
                        this.options.badgeListContainer.collection.fetch().done(function() {
                            self.options.badgeListContainer.render();
                        }).error(function() {
                            self.options.badgeListContainer.renderError();
                        });

                        this.tabbedView = new TabbedView({
                            tabs: tabs,
                            router: this.router,
                            viewLabel: gettext('Profile')
                        });

                        this.tabbedView.render();
                        this.$el.find('.account-settings-container').append(this.tabbedView.el);

                        if (this.firstRender) {
                            this.router.on('route:loadTab', _.bind(this.setActiveTab, this));
                            Backbone.history.start();
                            this.firstRender = false;
                            // Load from history.
                            this.router.navigate((Backbone.history.getFragment() || 'about_me'), {trigger: true});
                        } else {
                            // Restart the router so the tab will be brought up anew.
                            Backbone.history.stop();
                            Backbone.history.start();
                        }
                    } else {
                        this.$el.find('.wrapper-profile-section-container-two').append(this.sectionTwoView.render().el);
                    }
                    return this;
                },

                renderFields: function() {
                    var view = this,
                        fieldView,
                        imageView,
                        settings;

                    if (this.options.ownProfile) {
                        fieldView = this.options.accountPrivacyFieldView;
                        settings = this.options.accountSettingsModel;
                        fieldView.profileIsPrivate = !settings.get('year_of_birth');
                        fieldView.requiresParentalConsent = settings.get('requires_parental_consent');
                        fieldView.isAboveMinimumAge = settings.isAboveMinimumAge();
                        fieldView.undelegateEvents();
                        this.$('.wrapper-profile-field-account-privacy').append(fieldView.render().el);
                        fieldView.delegateEvents();
                    }

                    // Do not show name when in limited mode or no name has been set
                    if (this.showFullProfile() && this.options.accountSettingsModel.get('name')) {
                        this.$('.profile-section-one-fields').append(this.options.nameFieldView.render().el);
                    }
                    this.$('.profile-section-one-fields').append(this.options.usernameFieldView.render().el);

                    imageView = this.options.profileImageFieldView;
                    this.$('.profile-image-field').append(imageView.render().el);

                    if (this.showFullProfile()) {
                        _.each(this.options.sectionOneFieldViews, function(childFieldView) {
                            view.$('.profile-section-one-fields').append(childFieldView.render().el);
                        });
                    }
                },

                showLoadingError: function() {
                    this.$('.ui-loading-indicator').addClass('is-hidden');
                    this.$('.ui-loading-error').removeClass('is-hidden');
                }
            });

            return LearnerProfileView;
        });
}).call(this, define || RequireJS.define);
