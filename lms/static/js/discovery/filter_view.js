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
        templateId: '#filter-tpl',
        className: 'active-filter',

        initialize: function () {
            this.tpl = _.template($(this.templateId).html());
            this.listenTo(this.model, 'destroy', this.remove);
        },

        render: function () {
            this.className = this.model.get('type');
            this.$el.html(this.tpl(this.model.attributes));
            return this;
        },

        remove: function() {
            this.$el.remove();
        }

    });

});

})(define || RequireJS.define);
