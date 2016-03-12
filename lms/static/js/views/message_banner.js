(function(define) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!templates/fields/message_banner.underscore'
    ], function(gettext, $, _, Backbone, HtmlUtils, messageBannerTemplate) {
        var MessageBannerView = Backbone.View.extend({

            initialize: function(options) {
                this.options = _.defaults(options || {}, {urgency: 'high', type: ''});
            },

            render: function() {
                if (_.isUndefined(this.message) || _.isNull(this.message)) {
                    HtmlUtils.setHtml(this.$el, '');
                } else {
                    HtmlUtils.setHtml(
                        this.$el,
                        HtmlUtils.template(messageBannerTemplate)(
                            _.extend(this.options, {message: this.message})
                        )
                    );
                }
                return this;
            },

            showMessage: function(message) {
                this.message = message;
                this.render();
            },

            hideMessage: function() {
                this.message = null;
                this.render();
            }
        });

        return MessageBannerView;
    });
}).call(this, define || RequireJS.define);
