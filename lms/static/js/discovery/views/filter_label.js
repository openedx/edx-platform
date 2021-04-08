(function(define) {
    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, gettext, HtmlUtils) {
        'use strict';

        return Backbone.View.extend({

            tagName: 'li',
            templateId: '#filter-tpl',
            className: 'active-filter',

            initialize: function() {
                this.tpl = HtmlUtils.template($('#filter-tpl').html());
                this.listenTo(this.model, 'remove', this.remove);
                this.listenTo(this.model, 'change', this.render);
            },

            render: function() {
                var data = _.clone(this.model.attributes);
                data.name = data.name || data.query;
                this.className = data.type;
                HtmlUtils.setHtml(
                    this.$el,
                    this.tpl(data)
                );
                return this;
            }

        });
    });
}(define || RequireJS.define));
