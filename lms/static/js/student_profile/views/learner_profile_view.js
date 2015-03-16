;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var LearnerProfileView = Backbone.View.extend({

            initialize: function (options) {
                this.template = _.template($('#learner_profile-tpl').text());
            },

            render: function () {
                this.$el.html(this.template({
                    profileData: this.options.profileData
                }));
                this.$(".profile-data-userimage").html(this.options.profilePohotView.render().el);
                return this;
            }
        });

        return LearnerProfileView;
    })
}).call(this, define || RequireJS.define);