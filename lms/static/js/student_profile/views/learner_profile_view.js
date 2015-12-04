;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'text!templates/student_profile/learner_profile.underscore'],
        function (gettext, $, _, Backbone, learnerProfileTemplate) {

        var LearnerProfileView = Backbone.View.extend({

            initialize: function () {
                _.bindAll(this, 'showFullProfile', 'render', 'renderFields', 'showLoadingError');
                this.listenTo(this.options.preferencesModel, "change:" + 'account_privacy', this.render);
            },

            showFullProfile: function () {
                var isAboveMinimumAge = this.options.accountSettingsModel.isAboveMinimumAge();
                if (this.options.ownProfile) {
                    return isAboveMinimumAge && this.options.preferencesModel.get('account_privacy') === 'all_users';
                } else {
                    return this.options.accountSettingsModel.get('profile_is_public');
                }
            },

            render: function () {
                this.$el.html(_.template(learnerProfileTemplate, {
                    username: this.options.accountSettingsModel.get('username'),
                    ownProfile: this.options.ownProfile,
                    showFullProfile: this.showFullProfile()
                }));
                this.renderFields();
                return this;
            },

            renderFields: function() {
                var view = this;

                if (this.options.ownProfile) {
                    var fieldView = this.options.accountPrivacyFieldView,
                        settings = this.options.accountSettingsModel;
                    fieldView.profileIsPrivate =  !settings.get('year_of_birth');
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
                    _.each(this.options.sectionOneFieldViews, function (fieldView) {
                        view.$('.profile-section-one-fields').append(fieldView.render().el);
                    });

                    _.each(this.options.sectionTwoFieldViews, function (fieldView) {
                        view.$('.profile-section-two-fields').append(fieldView.render().el);
                    });
                }
            },

            showLoadingError: function () {
                this.$('.ui-loading-indicator').addClass('is-hidden');
                this.$('.ui-loading-error').removeClass('is-hidden');
            }
        });

        return LearnerProfileView;
    });
}).call(this, define || RequireJS.define);
