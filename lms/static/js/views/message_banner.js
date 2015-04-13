;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var MessageBannerView = Backbone.View.extend({

            initialize: function (options) {
                this.template = _.template($('#message_banner-tpl').text());
            },

            render: function () {
                if (this.message === null) {
                    this.$el.html('');
                } else {
                    this.$el.html(this.template({
                        message: this.message
                    }));
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
    })
}).call(this, define || RequireJS.define);
