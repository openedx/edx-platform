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
                message_div: '#certificate-white-list-editor .message',
                generate_exception_certificates_radio:
                    'input:radio[name=generate-exception-certificates-radio]:checked',

                events: {
                    'click #generate-exception-certificates': 'generateExceptionCertificates',
                    'click .delete-exception': 'removeException'
                },

                initialize: function(options){
                    this.certificateWhiteListEditorView = options.certificateWhiteListEditorView;
                    // Re-render the view when an item is added to the collection
                    this.listenTo(this.collection, 'change add remove', this.render);
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

                removeException: function(event){
                    // Delegate remove exception event to certificate white-list editor view
                    this.certificateWhiteListEditorView.trigger('removeException', $(event.target).data());

                    // avoid default click behavior of link by returning false.
                    return false;
                },

                generateExceptionCertificates: function(){
                    this.collection.sync(
                        {success: this.showSuccess(this), error: this.showError(this)},
                        $(this.generate_exception_certificates_radio).val()
                    );
                },

                showMessage: function(message, messageClass){
                    $(this.message_div).text(message).
                        removeClass('msg-error msg-success').addClass(messageClass).focus();
                    $('html, body').animate({
                        scrollTop: $(this.message_div).offset().top - 20
                    }, 1000);
                },

                showSuccess: function(caller_object){
                    return function(xhr){
                        caller_object.showMessage(xhr.message, 'msg-success');
                    };
                },

                showError: function(caller_object){
                    return function(xhr){
                        try{
                            var response = JSON.parse(xhr.responseText);
                            caller_object.showMessage(response.message, 'msg-error');
                        }
                        catch(exception){
                            caller_object.showMessage("Server Error, Please try again later.", 'msg-error');
                        }
                    };
                }
            });
        }
    );
}).call(this, define || RequireJS.define);