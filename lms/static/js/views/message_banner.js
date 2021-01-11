(function(define) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'backbone',
        'text!templates/fields/message_banner.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, $, _, Backbone, messageBannerTemplate, HtmlUtils) {
        var MessageBannerView = Backbone.View.extend({

            events: {
                'click #close': 'closeBanner'
            },

            closeBanner: function(event) {
                sessionStorage.setItem("isBannerClosed", true);
                this.hideMessage();
            },

            initialize: function(options) {
                if (_.isUndefined(options)) {
                    options = {};
                }
                this.options = _.defaults(options, {
                    urgency: 'high',
                    type: '',
                    hideCloseBtn: true,
                    isRecoveryEmailMsg: false,
                    isLearnerPortalEnabled: false
                });
            },

            render: function() {
                if (_.isUndefined(this.message) || _.isNull(this.message)) {
                    this.$el.html('');
                } else {
                    this.$el.html(_.template(messageBannerTemplate)(_.extend(this.options, {  // xss-lint: disable=javascript-jquery-html
                        message: this.message,
                        HtmlUtils: HtmlUtils
                    })));
                }
                return this;
            },

            showMessage: function(message) {
                this.message = message;
                if (sessionStorage.getItem("isBannerClosed") == null) {
                    this.render();
                }
            },

            hideMessage: function() {
                this.message = null;
                this.render();
            }
        });

        return MessageBannerView;
    });
}).call(this, define || RequireJS.define);
