(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/views/tabbed_view',
        'js/student_profile/views/section_two_tab',
        'text!templates/student_profile/learner_profile.underscore'],
        function(gettext, $, _, Backbone, HtmlUtils, TabbedView, SectionTwoTab, learnerProfileTemplate) {
            var LearnerProfileView = Backbone.View.extend({

                initialize: function(options) {
                    this.options = _.extend({}, options);
                    _.bindAll(this, 'showFullProfile', 'render', 'renderFields', 'showLoadingError');
                    this.listenTo(this.options.preferencesModel, 'change:' + 'account_privacy', this.render);
                    var Router = Backbone.Router.extend({
                        routes: {':about_me': 'loadTab', ':accomplishments': 'loadTab'}
                    });

                    this.router = new Router();
                    this.firstRender = true;
                },

                template: _.template(learnerProfileTemplate),

                showFullProfile: function() {
                    var isAboveMinimumAge = this.options.accountSettingsModel.isAboveMinimumAge();
                    if (this.options.ownProfile) {
                        return isAboveMinimumAge && this.options.preferencesModel.get('account_privacy') === 'all_users';
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
                    var self = this;

                    this.sectionTwoView = new SectionTwoTab({
                        viewList: this.options.sectionTwoFieldViews,
                        showFullProfile: this.showFullProfile,
                        ownProfile: this.options.ownProfile
                    });

                    var tabs = [
                    {view: this.sectionTwoView, title: gettext('About Me'), url: 'about_me'}
                    ];

                    HtmlUtils.setHtml(this.$el, HtmlUtils.template(learnerProfileTemplate)({
                        username: self.options.accountSettingsModel.get('username'),
                        ownProfile: self.options.ownProfile,
                        showFullProfile: self.showFullProfile()
                    }));
                    this.renderFields();

                    if (this.showFullProfile() && (this.options.accountSettingsModel.get('accomplishments_shared'))) {
                        tabs.push({
                            view: this.options.badgeListContainer,
                            title: gettext('Accomplishments'),
                            url: 'accomplishments'
                        });
                        this.options.badgeListContainer.collection.fetch().done(function() {
                            self.options.badgeListContainer.render();
                        }).error(function() {
                            self.options.badgeListContainer.renderError();
                        });
                    }
                    this.tabbedView = new TabbedView({
                        tabs: tabs,
                        router: this.router,
                        viewLabel: gettext('Profile')
                    });

                    this.tabbedView.render();

                    if (tabs.length === 1) {
                    // If the tab is unambiguous, don't display the tab interface.
                        this.tabbedView.$el.find('.page-content-nav').hide();
                    }

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


                    return this;
                },

                renderFields: function() {
                    var view = this;

                    if (this.options.ownProfile) {
                        var fieldView = this.options.accountPrivacyFieldView,
                            settings = this.options.accountSettingsModel;
                        fieldView.profileIsPrivate = !settings.get('year_of_birth');
                        fieldView.requiresParentalConsent = settings.get('requires_parental_consent');
                        fieldView.isAboveMinimumAge = settings.isAboveMinimumAge();
                        fieldView.undelegateEvents();
                        this.$('.wrapper-profile-field-account-privacy').append(fieldView.render().el);
                        fieldView.delegateEvents();
                    }

                    this.$('.profile-section-one-fields').append(this.options.usernameFieldView.render().el);

                    var imageView = this.options.profileImageFieldView;
                    this.$('.profile-image-field').append(imageView.render().el);

                    if (this.showFullProfile()) {
                        _.each(this.options.sectionOneFieldViews, function(fieldView) {
                            view.$('.profile-section-one-fields').append(fieldView.render().el);
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
