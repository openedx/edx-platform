;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var MessageBannerView = Backbone.View.extend({

            initialize: function (options) {
                if (_.isUndefined(options)) {
                    options = {};
                }
                this.options = _.defaults(options, {urgency: 'high', type: ''});
                this.template = _.template($('#message_banner-tpl').text());
            },

            render: function () {
                if (_.isUndefined(this.message) || _.isNull(this.message)) {
                    this.$el.html('');
                } else {
                    this.$el.html(this.template(_.extend(this.options, {
                        message: this.message
                    })));
                }
                return this;
            },

            showMessage: function (message) {
                this.message = message;
                this.render();
            },

            hideMessage: function () {
                this.message = null;
                this.render();
            }
        });

        return MessageBannerView;
    });
}).call(this, define || RequireJS.define);
