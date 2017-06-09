// Backbone Application View: CertificateWhiteList Editor View
/* global define, RequireJS */

(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'gettext',
        'backbone',
        'js/certificates/models/certificate_exception'
    ],
        function($, _, gettext, Backbone, CertificateExceptionModel) {
            return Backbone.View.extend({
                el: '#certificate-white-list-editor',
                message_div: '.message',

                events: {
                    'click #add-exception': 'addException'
                },

                render: function() {
                    var template = this.loadTemplate('certificate-white-list-editor');
                    this.$el.html(template());
                },

                loadTemplate: function(name) {
                    var templateSelector = '#' + name + '-tpl',
                        templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                addException: function() {
                    var value = this.$('#certificate-exception').val();
                    var notes = this.$('#notes').val();
                    var user_email = '', user_name = '', model = {};

                    if (this.isEmailAddress(value)) {
                        user_email = value;
                        model = {user_email: user_email};
                    }
                    else {
                        user_name = value;
                        model = {user_name: user_name};
                    }

                    var certificate_exception = new CertificateExceptionModel(
                        {
                            user_name: user_name,
                            user_email: user_email,
                            notes: notes,
                            new: true
                        },
                        {
                            url: this.collection.url
                        }
                    );
                    var message = '';

                    if (this.collection.findWhere(model)) {
                        message = gettext('<%= user %> already in exception list.');
                        this.escapeAndShowMessage(
                            _.template(message)({user: (user_name || user_email)})
                        );
                    }
                    else if (certificate_exception.isValid()) {
                        message = gettext('<%= user %> has been successfully added to the exception list. Click Generate Exception Certificate below to send the certificate.');  // eslint-disable-line max-len
                        certificate_exception.save(
                            null,
                            {
                                success: this.showSuccess(
                                    this,
                                    true,
                                    _.template(message)({user: (user_name || user_email)})
                                ),
                                error: this.showError(this)
                            }
                        );
                    }
                    else {
                        this.escapeAndShowMessage(certificate_exception.validationError);
                    }
                },

                isEmailAddress: function validateEmail(email) {
                    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                    return re.test(email);
                },

                escapeAndShowMessage: function(message) {
                    $(this.message_div + '>p').remove();
                    this.$(this.message_div).removeClass('hidden').append('<p>' + _.escape(message) + '</p>');
                },

                showSuccess: function(caller, add_model, message) {
                    return function(model) {
                        if (add_model) {
                            caller.collection.add(model);
                        }
                        caller.escapeAndShowMessage(message);
                    };
                },

                showError: function(caller) {
                    return function(model, response) {
                        try {
                            var response_data = JSON.parse(response.responseText);
                            caller.escapeAndShowMessage(response_data.message);
                        }
                        catch (exception) {
                            caller.escapeAndShowMessage(
                                gettext('Server Error, Please refresh the page and try again.')
                            );
                        }
                    };
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
