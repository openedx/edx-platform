;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone'
    ], function (gettext, $, _, Backbone) {

        var LearnerProfileImageView = Backbone.View.extend({

            initialize: function (options) {
            },

            render: function () {
                return this;
            }
        });

        return LearnerProfileImageView;
    })
}).call(this, define || RequireJS.define);