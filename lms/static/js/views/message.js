;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        return Backbone.View.extend({

            initialize: function (options) {
                var templateId = _.isUndefined(options.templateId) ? '#message_view-tpl' : options.templateId;
                this.template = _.template($(templateId).text());
            },

            render: function () {
                if (_.isUndefined(this.message) || _.isNull(this.message)) {
                    this.$el.html('');
                } else {
                    this.$el.html(this.template({
                        message: this.message,
                        icon: this.icon
                    }));
                }
                return this;
            },

            showMessage: function (message, icon) {
                this.message = message;
                this.icon = icon;
                this.render();
            },

            hideMessage: function () {
                this.message = null;
                this.render();
            }
        });
    });
}).call(this, define || RequireJS.define);
