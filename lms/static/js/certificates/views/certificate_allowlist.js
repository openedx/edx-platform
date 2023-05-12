// Backbone Application View: CertificateAllowlist View
/* global define, RequireJS */

(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'gettext',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils'
    ],

    function($, _, gettext, Backbone, HtmlUtils) {
        return Backbone.View.extend({
            el: '#allowlisted-students',
            message_div: 'div.allowlisted-students > div.message',
            generate_exception_certificates_radio:
                    'input:radio[name=generate-exception-certificates-radio]:checked',

            events: {
                'click #generate-exception-certificates': 'generateExceptionCertificates',
                'click .delete-exception': 'removeException'
            },

            initialize: function(options) {
                this.certificateAllowlistEditorView = options.certificateAllowlistEditorView;
                this.active_certificate = options.active_certificate;
                // Re-render the view when an item is added to the collection
                this.listenTo(this.collection, 'change add remove', this.render);
            },

            render: function() {
                // eslint-disable-next-line no-var
                var template = this.loadTemplate('certificate-allowlist');
                this.$el.html(HtmlUtils.HTML(template({certificates: this.collection.models})).toString());
                if (!this.active_certificate || this.collection.isEmpty()) {
                    this.$('#generate-exception-certificates').attr('disabled', 'disabled');
                } else {
                    this.$('#generate-exception-certificates').removeAttr('disabled');
                }
            },

            loadTemplate: function(name) {
                // eslint-disable-next-line no-var
                var templateSelector = '#' + name + '-tpl',
                    templateText = $(templateSelector).text();
                return _.template(templateText);
            },

            removeException: function(event) {
                // eslint-disable-next-line no-var
                var certificate = $(event.target).data();
                // eslint-disable-next-line no-var
                var model = this.collection.findWhere(certificate);
                // eslint-disable-next-line no-var
                var self = this;
                if (model) {
                    model.destroy(
                        {
                            success: function() {
                                self.escapeAndShowMessage(
                                    gettext('Student Removed from certificate allowlist successfully.')
                                );
                            },
                            error: this.showError(this),
                            wait: true,
                            data: JSON.stringify(model.attributes)
                        }
                    );
                } else {
                    this.escapeAndShowMessage(
                        gettext('Could not find Certificate Exception in the allowlist. Please refresh the page and try again') // eslint-disable-line max-len
                    );
                }
            },

            generateExceptionCertificates: function() {
                this.collection.sync(
                    {success: this.showSuccess(this), error: this.showError(this)},
                    $(this.generate_exception_certificates_radio).val()
                );
            },

            escapeAndShowMessage: function(message) {
                $(this.message_div + '>p').remove();
                // xss-lint: disable=javascript-jquery-append
                $(this.message_div).removeClass('hidden').append(HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<p>'),
                    _.escape(message),
                    HtmlUtils.HTML('</p>')
                ))
                    .focus();
                $(this.message_div).fadeOut(6000, 'linear');
            },

            // eslint-disable-next-line camelcase
            showSuccess: function(caller_object) {
                return function(xhr) {
                    // eslint-disable-next-line camelcase
                    caller_object.escapeAndShowMessage(xhr.message);
                };
            },

            // eslint-disable-next-line camelcase
            showError: function(caller_object) {
                return function(xhr) {
                    try {
                        // eslint-disable-next-line no-var
                        var response = JSON.parse(xhr.responseText);
                        // eslint-disable-next-line camelcase
                        caller_object.escapeAndShowMessage(response.message);
                    } catch (exception) {
                        // eslint-disable-next-line camelcase
                        caller_object.escapeAndShowMessage(
                            gettext('Server Error, Please refresh the page and try again.')
                        );
                    }
                };
            }
        });
    }
    );
}).call(this, define || RequireJS.define);
