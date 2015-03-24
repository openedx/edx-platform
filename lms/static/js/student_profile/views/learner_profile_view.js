;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var LearnerProfileView = Backbone.View.extend({

            initialize: function (options) {
                this.template = _.template($('#learner_profile-tpl').text());
                _.bindAll(this, 'showFullProfile', 'render', 'renderFields', 'showLoadingError');
                this.listenTo(this.options.preferencesModel, "change:" + 'account_privacy', this.render);
            },

            showFullProfile: function () {
                if (this.options.own_profile) {
                    return this.options.preferencesModel.get('account_privacy') === 'all_users';
                } else {
                    return this.options.accountSettingsModel.get('profile_is_public');
                }
            },

            render: function () {
                this.$el.html(this.template({
                    profilePhoto: 'http://www.teachthought.com/wp-content/uploads/2012/07/edX-120x120.jpg',
                    ownProfile: this.options.own_profile,
                    showFullProfile: this.showFullProfile()
                }));
                this.renderFields();
                return this;
            },

            renderFields: function() {
                var view = this;

                if (this.options.own_profile) {
                    var fieldView = this.options.accountPrivacyFieldView;
                    fieldView.profileIsPrivate =  (!this.options.accountSettingsModel.get('year_of_birth'));
                    fieldView.undelegateEvents();
                    this.$('.wrapper-profile-field-account-privacy').append(fieldView.render().el);
                    fieldView.delegateEvents();
                }

                this.$('.profile-section-one-fields').append(this.options.usernameFieldView.render().el);

                if (this.showFullProfile()) {
                    _.each(this.options.sectionOneFieldViews, function (fieldView, index) {
                        fieldView.undelegateEvents();
                        view.$('.profile-section-one-fields').append(fieldView.render().el);
                        fieldView.delegateEvents();
                    });

                    _.each(this.options.sectionTwoFieldViews, function (fieldView, index) {
                        fieldView.undelegateEvents();
                        view.$('.profile-section-two-fields').append(fieldView.render().el);
                        fieldView.delegateEvents();
                    });
                }
            },
            showLoadingError: function () {
                this.$('.ui-loading-indicator').addClass('is-hidden');
                this.$('.ui-loading-error').removeClass('is-hidden');
            }
        });

        return LearnerProfileView;
    })
}).call(this, define || RequireJS.define);
