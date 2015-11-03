// Backbone Application View: CertificateWhitelist View
/*global define, RequireJS */

;(function(define){
    'use strict';

    define([
            'jquery',
            'underscore',
            'gettext',
            'backbone'
        ],

        function($, _, gettext, Backbone){
            return Backbone.View.extend({
                el: "#white-listed-students",
                generate_exception_certificates_radio:
                    'input:radio[name=generate-exception-certificates-radio]:checked',

                events: {
                    'click #generate-exception-certificates': 'generateExceptionCertificates'
                },

                initialize: function(){
                    // Re-render the view when an item is added to the collection
                    this.listenTo(this.collection, 'change add', this.render);
                },

                render: function(){
                    var template = this.loadTemplate('certificate-white-list');
                    this.$el.html(template({certificates: this.collection.models}));

                },

                loadTemplate: function(name) {
                    var templateSelector = "#" + name + "-tpl",
                    templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                generateExceptionCertificates: function(){
                    this.collection.sync(
                        {success: this.showSuccess(this), error: this.showError(this)},
                        $(this.generate_exception_certificates_radio).val()
                    );
                },

                showSuccess: function(caller_object){
                    return function(xhr){
                        var response = xhr;
                        $(".message").text(response.message).removeClass('msg-error').addClass('msg-success').focus();
                        caller_object.collection.update(JSON.parse(response.data));
                        $('html, body').animate({
                            scrollTop: $("#certificate-exception").offset().top - 10
                        }, 1000);
                    };
                },

                showError: function(caller_object){
                    return function(xhr){
                        var response = JSON.parse(xhr.responseText);
                        $(".message").text(response.message).removeClass('msg-success').addClass("msg-error").focus();
                        caller_object.collection.update(JSON.parse(response.data));
                        $('html, body').animate({
                            scrollTop: $("#certificate-exception").offset().top - 10
                        }, 1000);
                    };
                }
            });
        }
    );
}).call(this, define || RequireJS.define);