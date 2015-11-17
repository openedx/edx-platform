// Backbone Application View: CertificateWhiteList Editor View
/*global define, RequireJS */

;(function(define){
    'use strict';
    define([
            'jquery',
            'underscore',
            'gettext',
            'backbone',
            'js/certificates/models/certificate_exception'
        ],
        function($, _, gettext, Backbone, CertificateExceptionModel){
            return Backbone.View.extend({
                el: "#certificate-white-list-editor",
                message_div: '.message',

                events: {
                    'click #add-exception': 'addException'
                },

                initialize: function(){
                    this.on('removeException', this.removeException);
                },


                render: function(){
                    var template = this.loadTemplate('certificate-white-list-editor');
                    this.$el.html(template());
                },

                loadTemplate: function(name) {
                    var templateSelector = "#" + name + "-tpl",
                    templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                addException: function(){
                    var value = this.$("#certificate-exception").val();
                    var notes = this.$("#notes").val();
                    var user_email = '', user_name='', model={};

                    if(this.isEmailAddress(value)){
                        user_email = value;
                        model = {user_email: user_email};
                    }
                    else{
                        user_name = value;
                        model = {user_name: user_name};
                    }

                    var certificate_exception = new CertificateExceptionModel({
                        url: this.collection.url,
                        user_name: user_name,
                        user_email: user_email,
                        notes: notes,
                        new: true
                    });

                    if(this.collection.findWhere(model)){
                        this.showMessage("username/email already in exception list", 'msg-error');
                    }
                    else if(certificate_exception.isValid()){
                        certificate_exception.save(
                            null,
                            {
                                success: this.showSuccess(
                                    this,
                                    true,
                                    'Students added to Certificate white list successfully'
                                ),
                                error: this.showError(this)
                            }
                        );

                    }
                    else{
                        this.showMessage(certificate_exception.validationError, 'msg-error');
                    }
                },

                removeException: function(certificate){
                    var model = this.collection.findWhere(certificate);
                    if(model){
                        model.destroy(
                            {
                                success: this.showSuccess(
                                    this,
                                    false,
                                    'Student Removed from certificate white list successfully.'
                                ),
                                error: this.showError(this),
                                wait: true,
                                //emulateJSON: true,
                                data: JSON.stringify(model.attributes)
                            }
                        );
                        this.showMessage('Exception is being removed from server.', 'msg-success');
                    }
                    else{
                        this.showMessage('Could not find Certificate Exception in white list.', 'msg-error');
                    }
                },

                isEmailAddress: function validateEmail(email) {
                    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                    return re.test(email);
                },

                showMessage: function(message, messageClass){
                    this.$(this.message_div).text(message).
                        removeClass('msg-error msg-success').addClass(messageClass).focus();
                    $('html, body').animate({
                        scrollTop: this.$el.offset().top - 20
                    }, 1000);
                },

                showSuccess: function(caller, add_model, message){
                    return function(model){
                        if(add_model){
                            caller.collection.add(model);
                        }
                        caller.showMessage(message, 'msg-success');
                    };
                },

                showError: function(caller){
                    return function(model, response){
                        try{
                            var response_data = JSON.parse(response.responseText);
                            caller.showMessage(response_data.message, 'msg-error');
                        }
                        catch(exception){
                            caller.showMessage("Server Error, Please try again later.", 'msg-error');
                        }
                    };
                }
            });
        }
    );
}).call(this, define || RequireJS.define);