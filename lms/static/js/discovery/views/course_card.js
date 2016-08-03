;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'date',
    'edx-ui-toolkit/js/utils/html-utils',
    'text!templates/discovery/course_card.underscore'
], function ($, _, Backbone, gettext, Date, HtmlUtils, CourseCardTemplate) {
    'use strict';

    function formatDate(date) {
        return dateUTC(date).toString('MMM dd, yyyy');
    }

    // Return a date object using UTC time instead of local time
    function dateUTC(date) {
        return new Date(
            date.getUTCFullYear(),
            date.getUTCMonth(),
            date.getUTCDate(),
            date.getUTCHours(),
            date.getUTCMinutes(),
            date.getUTCSeconds()
        );
    }

    return Backbone.View.extend({

        tagName: 'li',
        templateId: '#course_card-tpl',
        className: 'courses-listing-item',

        initialize: function () {
            this.tpl = HtmlUtils.template(CourseCardTemplate);
        },

        render: function () {
            var data = _.clone(this.model.attributes);
            data.start = formatDate(new Date(data.start));
            data.enrollment_start = formatDate(new Date(data.enrollment_start));
            HtmlUtils.setHtml(this.$el, this.tpl(data));
            return this;
        }

    });

});

})(define || RequireJS.define);
