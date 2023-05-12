// Backbone Application View: CertificateInvalidationView
/* global define, RequireJS */

(function(define) {
    'use strict';

    define(
        ['jquery', 'underscore', 'gettext', 'backbone', 'js/certificates/models/certificate_invalidation'],

        function($, _, gettext, Backbone, CertificateInvalidationModel) {
            return Backbone.View.extend({
                el: '#certificate-invalidation',
                messages: 'div.message',
                events: {
                    'click #invalidate-certificate': 'invalidateCertificate',
                    'click .re-validate-certificate': 'reValidateCertificate'
                },

                initialize: function() {
                    this.listenTo(this.collection, 'change add remove', this.render);
                },

                render: function() {
                    // eslint-disable-next-line no-var
                    var template = this.loadTemplate('certificate-invalidation');
                    this.$el.html(template({certificate_invalidations: this.collection.models}));
                },

                loadTemplate: function(name) {
                    // eslint-disable-next-line no-var
                    var templateSelector = '#' + name + '-tpl',
                        templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                invalidateCertificate: function() {
                    // eslint-disable-next-line no-var
                    var user = this.$('#certificate-invalidation-user').val();
                    // eslint-disable-next-line no-var
                    var notes = this.$('#certificate-invalidation-notes').val();
                    // eslint-disable-next-line no-var
                    var message = '';

                    /* eslint-disable-next-line camelcase, no-var */
                    var certificate_invalidation = new CertificateInvalidationModel(
                        {
                            user: user,
                            notes: notes
                        },
                        {
                            url: this.collection.url
                        }
                    );

                    if (this.collection.findWhere({user: user})) {
                        message = gettext('Certificate of <%= user %> has already been invalidated. Please check your spelling and retry.'); // eslint-disable-line max-len
                        this.escapeAndShowMessage(_.template(message)({user: user}));
                    // eslint-disable-next-line camelcase
                    } else if (certificate_invalidation.isValid()) {
                        // eslint-disable-next-line no-var
                        var self = this;
                        // eslint-disable-next-line camelcase
                        certificate_invalidation.save(null, {
                            wait: true,

                            success: function(model) {
                                self.collection.add(model);
                                message = gettext('Certificate has been successfully invalidated for <%= user %>.');
                                self.escapeAndShowMessage(_.template(message)({user: user}));
                            },

                            error: function(model, response) {
                                try {
                                    /* eslint-disable-next-line camelcase, no-var */
                                    var response_data = JSON.parse(response.responseText);
                                    // eslint-disable-next-line camelcase
                                    self.escapeAndShowMessage(response_data.message);
                                } catch (exception) {
                                    self.escapeAndShowMessage(
                                        gettext('Server Error, Please refresh the page and try again.')
                                    );
                                }
                            }
                        });
                    } else {
                        // eslint-disable-next-line camelcase
                        this.escapeAndShowMessage(certificate_invalidation.validationError);
                    }
                },

                reValidateCertificate: function(event) {
                    /* eslint-disable-next-line camelcase, no-var */
                    var certificate_invalidation = $(event.target).data();
                    // eslint-disable-next-line no-var
                    var model = this.collection.get(certificate_invalidation),
                        self = this;

                    if (model) {
                        model.destroy({
                            success: function() {
                                self.escapeAndShowMessage(
                                    gettext('The certificate for this learner has been re-validated and the system is re-running the grade for this learner.') // eslint-disable-line max-len
                                );
                            },
                            // eslint-disable-next-line no-shadow
                            error: function(model, response) {
                                try {
                                    /* eslint-disable-next-line camelcase, no-var */
                                    var response_data = JSON.parse(response.responseText);
                                    // eslint-disable-next-line camelcase
                                    self.escapeAndShowMessage(response_data.message);
                                } catch (exception) {
                                    self.escapeAndShowMessage(
                                        gettext('Server Error, Please refresh the page and try again.')
                                    );
                                }
                            },
                            wait: true,
                            data: JSON.stringify(model.attributes)
                        });
                    } else {
                        self.escapeAndShowMessage(
                            gettext('Could not find Certificate Invalidation in the list. Please refresh the page and try again') // eslint-disable-line max-len
                        );
                    }
                },

                isEmailAddress: function validateEmail(email) {
                    // eslint-disable-next-line no-var
                    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                    return re.test(email);
                },

                escapeAndShowMessage: function(message) {
                    $(this.messages + '>p').remove();
                    this.$(this.messages).removeClass('hidden').append('<p>' + _.escape(message) + '</p>');
                }

            });
        }
    );
}).call(this, define || RequireJS.define);
