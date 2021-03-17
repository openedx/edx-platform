(function(define) {
    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/date-utils',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, gettext, DateUtils, HtmlUtils) {
        'use strict';

        function formatDate(date, userLanguage, userTimezone) {
            var context;
            context = {
                datetime: date,
                language: userLanguage,
                timezone: userTimezone,
                format: DateUtils.dateFormatEnum.shortDate
            };
            return DateUtils.localize(context);
        }

        return Backbone.View.extend({

            tagName: 'li',
            templateId: '#course_card-tpl',
            className: 'courses-listing-item',

            initialize: function() {
                this.tpl = HtmlUtils.template($(this.templateId).html());
            },

            render: function() {
                var data = _.clone(this.model.attributes);
                var userLanguage = '',
                    userTimezone = '';
                if (this.model.userPreferences !== undefined) {
                    userLanguage = this.model.userPreferences.userLanguage;
                    userTimezone = this.model.userPreferences.userTimezone;
                }
                if (data.advertised_start !== undefined) {
                    data.start = data.advertised_start;
                } else {
                    data.start = formatDate(
                        new Date(data.start),
                        userLanguage,
                        userTimezone
                    );
                }
                data.enrollment_start = formatDate(
                    new Date(data.enrollment_start),
                    userLanguage,
                    userTimezone
                );
                HtmlUtils.setHtml(
                    this.$el,
                    this.tpl(data)
                );
                return this;
            }

        });
    });
}(define || RequireJS.define));
