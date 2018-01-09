(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'moment',
        'edx-ui-toolkit/js/utils/html-utils',
        'support/js/models/manage_user',
        'text!support/templates/manage_user.underscore'
    ], function(Backbone, _, moment, HtmlUtils, ManageUserModel, manageUserTemplate) {
        return Backbone.View.extend({
            manageUserTpl: HtmlUtils.template(manageUserTemplate),

            events: {
                'submit .manage-user-form': 'search',
                'click .disable-account-btn': 'disableAccount'
            },
            initialize: function(options) {
                var user = options.user;
                this.initialUser = user;
                this.userSupportUrl = options.userSupportUrl;
                this.user_profile = new ManageUserModel({
                    user: user,
                    baseUrl: options.userDetailUrl
                });
                this.user_profile.on('change', _.bind(this.render, this));
            },
            render: function() {
                var user = this.user_profile.user;
                HtmlUtils.setHtml(this.$el, this.manageUserTpl({
                    user: user,
                    user_profile: this.user_profile,
                    formatDate: function(date) {
                        return date ? moment.utc(date).format('lll z') : 'N/A';
                    }
                }));

                this.checkInitialSearch();
                return this;
            },

            /*
             * Check if the URL has provided an initial search, and
             * perform that search if so.
             */
            checkInitialSearch: function() {
                if (this.initialUser) {
                    delete this.initialUser;
                    this.$('.manage-user-form').submit();
                }
            },

            /*
             * Return the user's search string.
             */
            getSearchString: function() {
                return this.$('#manage-user-query-input').val();
            },

            /*
             * Perform the search. Renders the view on success.
             */
            search: function(event) {
                event.preventDefault();
                this.user_profile.user = this.getSearchString();
                this.user_profile.fetch({
                    success: _.bind(function() {
                        this.user_profile.set('response', '');
                        this.user_profile.set(
                            'date_joined',
                            moment(this.user_profile.get('date_joined')).format('YYYY-MM-DD')
                        );
                        this.render();
                    }, this)
                });
            },
            disableAccount: function() {
                this.user_profile.disableAccount();
            }
        });
    });
}).call(this, define || RequireJS.define);
