/**
 * Display top-level errors in the payment/verification flow.
 */
 var edx = edx || {};

 (function($, _, Backbone) {
     'use strict';

     edx.verify_student = edx.verify_student || {};

     edx.verify_student.ErrorView = Backbone.View.extend({

         initialize: function(obj) {
             var ErrorModel = Backbone.Model.extend({});
             this.model = obj.model || new ErrorModel({
                 errorTitle: '',
                 errorMsg: '',
                 shown: false
             });
             this.listenTo(this.model, 'change', this.render);
         },

         render: function() {
             var renderedHtml = edx.HtmlUtils.template($('#error-tpl').html())(
                 {
                     errorTitle: this.model.get('errorTitle'),
                     errorMsg: this.model.get('errorMsg')
                 }
            );
             edx.HtmlUtils.setHtml(
                 $(this.el),
                 renderedHtml
             );

             if (this.model.get('shown')) {
                 $(this.el).show();
                 $('html, body').animate({scrollTop: 0});
             } else {
                 $(this.el).hide();
             }
         }
     });
 }($, _, Backbone));
