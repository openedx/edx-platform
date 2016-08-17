;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
], function ($, _, Backbone, gettext) {
    'use strict';

    return Backbone.View.extend({

        tagName: 'li',
        templateId: '#search_facet-tpl',
        className: '',

        initialize: function () {
            this.tpl = _.template($(this.templateId).html());
        },

        render: function (type, name, term, count) {
            this.$el.html(this.tpl({name: name, term: term, count: count}));
            this.$el.attr('data-facet', type);
            return this;
        },

        remove: function() {
            this.stopListening();
            this.$el.remove();
        }

    });

});

})(define || RequireJS.define);
