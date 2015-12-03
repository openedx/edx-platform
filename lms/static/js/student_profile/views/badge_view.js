;(function (define, undefined) {
    'use strict';
    define([
            'gettext', 'jquery', 'underscore', 'backbone', 'moment', 'text!templates/student_profile/badge.underscore'],
        function (gettext, $, _, Backbone, Moment, badgeTemplate) {

            var BadgeView = Backbone.View.extend({
                attributes: {
                    'class': 'badge-display'
                },
                render: function () {
                    var context = _.extend(this.options.model.toJSON(), {
                        'created': new Moment(this.options.model.toJSON().created)
                    });
                    this.$el.html(_.template(badgeTemplate, context));
                    return this;
                }
            });

            return BadgeView;
        });
}).call(this, define || RequireJS.define);
