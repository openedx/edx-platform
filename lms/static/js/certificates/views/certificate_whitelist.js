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
                message_div: 'div.white-listed-students > div.message',
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
                    var certificate = $(event.target).data();
                    var model = this.collection.findWhere(certificate);
                    var self = this;
                    if(model){
                        model.destroy(
                            {
                                success: function() {
                                    self.showMessage('Student Removed from certificate white list successfully.');
                                },
                                error: this.showError(this),
                                wait: true,
                                data: JSON.stringify(model.attributes)
                            }
                        );
                    }
                    else{
                        this.showMessage(
                            'Could not find Certificate Exception in white list. ' +
                            'Please refresh the page and try again'
                        );
                    }
                },

                generateExceptionCertificates: function(){
                    this.collection.sync(
                        {success: this.showSuccess(this), error: this.showError(this)},
                        $(this.generate_exception_certificates_radio).val()
                    );
                },

                showMessage: function(message){
                    $(this.message_div +  ">p" ).remove();
                    $(this.message_div).removeClass('hidden').append("<p>"+ gettext(message) + "</p>").focus();
                    $(this.message_div).fadeOut(6000, "linear");
                },

                showSuccess: function(caller_object){
                    return function(xhr){
                        caller_object.showMessage(xhr.message);
                    };
                },

                showError: function(caller_object){
                    return function(xhr){
                        try{
                            var response = JSON.parse(xhr.responseText);
                            caller_object.showMessage(response.message);
                        }
                        catch(exception){
                            caller_object.showMessage(
                                "Server Error, Please refresh the page and try again.");
                        }
                    };
                }
            });
        }
    );
}).call(this, define || RequireJS.define);