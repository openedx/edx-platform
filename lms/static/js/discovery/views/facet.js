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
            templateId: '#search_facet-tpl',
            className: '',

            initialize: function() {
                this.tpl = HtmlUtils.template($(this.templateId).html());
            },

            render: function(type, name, term, count) {
                HtmlUtils.setHtml(
                    this.$el,
                    this.tpl({name: name, term: term, count: count})
                );
                this.$el.attr('data-facet', type);
                return this;
            },

            remove: function() {
                this.stopListening();
                this.$el.remove();
            }

        });
    });
}(define || RequireJS.define));
