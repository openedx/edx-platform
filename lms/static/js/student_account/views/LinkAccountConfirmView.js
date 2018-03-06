(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'backbone',
        'js/student_account/views/LinkAccountBaseView',
        'text!templates/student_account/link_account_confirm.underscore',
        'edx-ui-toolkit/js/utils/string-utils',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, LinkAccountBaseView, linkAccountConfirmTpl, StringUtils, HtmlUtils) {
        return LinkAccountBaseView.extend({
            el: '#link-account-confirm-main',
            events: {
                'click .link-account-disconnect': 'disconnect',
                'click .link-account-button': 'confirm'
            },
            initialize: function(options) {
                this.options = _.extend({}, options);
            },
            render: function() {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(linkAccountConfirmTpl)({
                    newFullName: this.options.newFullName,
                    newEmail: this.options.newEmail,
                    message: ''
                }));
                return this;
            },
            disconnect: function() {
                var data = {};
                var view = this;
                // Disconnects the provider from the user's edX account.
                // See python-social-auth docs for more information.
                $.ajax({
                    type: 'POST',
                    url: this.options.disconnectUrl,
                    data: data,
                    dataType: 'html',
                    success: function() {
                        view.redirect_to('/logout?msa_only=true');
                    },
                    error: function() {
                        view.showError('There was an error disconnecting your account.');
                    }
                });
            },
            confirm: function() {
                var defaultOptions;
                var view = this;
                var defaultErrorMessage = 'There was an error upgrading your account. ';
                if (this.options.userData) {
                    defaultOptions = {
                        contentType: 'application/merge-patch+json',
                        patch: true,
                        wait: true,
                        success: function() {
                            view.redirect_to('/dashboard');
                        },
                        error: function(model, error) {
                            var msg = defaultErrorMessage;
                            var json = error.responseJSON;
                            if (json.field_errors && json.field_errors.email) {
                                msg += json.field_errors.email.user_message;
                            }
                            view.showError(msg);
                        }
                    };
                    this.model.save(this.options.userData, defaultOptions);
                } else {
                    view.showError(defaultErrorMessage);
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
