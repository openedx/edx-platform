(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'text!../../../templates/learner_dashboard/certificate_list.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             certificateTpl
         ) {
             return Backbone.View.extend({
                 tpl: _.template(certificateTpl),

                 initialize: function(options) {
                     this.title = options.title || false;
                     this.render();
                 },

                 render: function() {
                     var data = {
                         title: this.title,
                         certificateList: this.collection.toJSON()
                     };

                     this.$el.html(this.tpl(data));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
