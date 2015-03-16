;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var LearnerProfilePhotoView = Backbone.View.extend({

            initialize: function (options) {
                this.template = _.template($('#learner_profile-tpl').text());
                this.profileData = options.profileData;
            },

            render: function () {
                this.$el.html(this.template({
                }));
                return this;
            }
        });

        return LearnerProfilePhotoView;
    })
}).call(this, define || RequireJS.define);