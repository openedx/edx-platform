;(function (define, undefined) {
    'use strict';
    define([
            'gettext', 'jquery', 'underscore', 'backbone', 'moment', 'text!templates/student_profile/badge.underscore'],
        function (gettext, $, _, Backbone, Moment, badgeTemplate) {

            var BadgeView = Backbone.View.extend({
                attributes: {
                    'class': 'badge-display'
                },
                template: _.template(badgeTemplate),
                render: function () {
                    var context = _.extend(this.options.model.toJSON(), {
                        'created': new Moment(this.options.model.toJSON().created)
                    });
                    this.$el.html(this.template(context));
                    return this;
                }
            });

            return BadgeView;
        });
}).call(this, define || RequireJS.define);
