/**
 * A generic header view class.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'text!templates/components/header/header.underscore'],
           function (Backbone, headerTemplate) {
               var HeaderView = Backbone.View.extend({
                   initialize: function (options) {
                       this.template = _.template(headerTemplate);
                       this.listenTo(this.model, 'change', this.render);
                       this.render();
                   },

                   render: function () {
                       var json = this.model.attributes;
                       this.$el.html(this.template(json));
                       return this;
                   }
               });

               return HeaderView;
           });
}).call(this, define || RequireJS.define);
