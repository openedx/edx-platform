// Backbone Application View: CertificateAllowlist Editor View
/* global define, RequireJS */

(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'gettext',
        'backbone',
        'js/certificates/models/certificate_exception',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
    function($, _, gettext, Backbone, CertificateExceptionModel, HtmlUtils) {
        return Backbone.View.extend({
            el: '#certificate-allowlist-editor',
            message_div: '.message',

            events: {
                'click #add-exception': 'addException'
            },

            render: function() {
                // eslint-disable-next-line no-var
                var template = this.loadTemplate('certificate-allowlist-editor');
                this.$el.html(HtmlUtils.HTML(template()).toString());
            },

            loadTemplate: function(name) {
                // eslint-disable-next-line no-var
                var templateSelector = '#' + name + '-tpl',
                    templateText = $(templateSelector).text();
                return _.template(templateText);
            },

            addException: function() {
                // eslint-disable-next-line no-var
                var value = this.$('#certificate-exception').val();
                // eslint-disable-next-line no-var
                var notes = this.$('#notes').val();
                /* eslint-disable-next-line camelcase, no-var */
                var user_email = '',
                    // eslint-disable-next-line camelcase
                    user_name = '',
                    model = {};

                if (this.isEmailAddress(value)) {
                    // eslint-disable-next-line camelcase
                    user_email = value;
                    // eslint-disable-next-line camelcase
                    model = {user_email: user_email};
                } else {
                    // eslint-disable-next-line camelcase
                    user_name = value;
                    // eslint-disable-next-line camelcase
                    model = {user_name: user_name};
                }

                /* eslint-disable-next-line camelcase, no-var */
                var certificate_exception = new CertificateExceptionModel(
                    {
                        // eslint-disable-next-line camelcase
                        user_name: user_name,
                        // eslint-disable-next-line camelcase
                        user_email: user_email,
                        notes: notes,
                        new: true
                    },
                    {
                        url: this.collection.url
                    }
                );
                // eslint-disable-next-line no-var
                var message = '';

                if (this.collection.findWhere(model)) {
                    message = gettext('<%- user %> already in exception list.');
                    this.escapeAndShowMessage(
                        // eslint-disable-next-line camelcase
                        _.template(message)({user: (user_name || user_email)})
                    );
                // eslint-disable-next-line camelcase
                } else if (certificate_exception.isValid()) {
                    message = gettext('<%- user %> has been successfully added to the exception list. Click Generate Exception Certificate below to send the certificate.'); // eslint-disable-line max-len
                    // eslint-disable-next-line camelcase
                    certificate_exception.save(
                        null,
                        {
                            success: this.showSuccess(
                                this,
                                true,
                                // eslint-disable-next-line camelcase
                                _.template(message)({user: (user_name || user_email)})
                            ),
                            error: this.showError(this)
                        }
                    );
                } else {
                    // eslint-disable-next-line camelcase
                    this.escapeAndShowMessage(certificate_exception.validationError);
                }
            },

            isEmailAddress: function validateEmail(email) {
                // eslint-disable-next-line no-var
                var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                return re.test(email);
            },

            escapeAndShowMessage: function(message) {
                $(this.message_div + '>p').remove();
                // eslint-disable-next-line max-len
                this.$(this.message_div).removeClass('hidden').append(HtmlUtils.joinHtml(HtmlUtils.HTML('<p>'), message, HtmlUtils.HTML('</p>')).toString());
            },

            // eslint-disable-next-line camelcase
            showSuccess: function(caller, add_model, message) {
                return function(model) {
                    // eslint-disable-next-line camelcase
                    if (add_model) {
                        caller.collection.add(model);
                    }
                    caller.escapeAndShowMessage(message);
                };
            },

            showError: function(caller) {
                return function(model, response) {
                    try {
                        /* eslint-disable-next-line camelcase, no-var */
                        var response_data = JSON.parse(response.responseText);
                        // eslint-disable-next-line camelcase
                        caller.escapeAndShowMessage(response_data.message);
                    } catch (exception) {
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
