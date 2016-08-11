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
                    var template = this.loadTemplate('certificate-invalidation');
                    this.$el.html(template({certificate_invalidations: this.collection.models}));
                },

                loadTemplate: function(name) {
                    var templateSelector = '#' + name + '-tpl',
                        templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                invalidateCertificate: function() {
                    var user = this.$('#certificate-invalidation-user').val();
                    var notes = this.$('#certificate-invalidation-notes').val();
                    var message = '';

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
                        message = gettext('Certificate of <%= user %> has already been invalidated. Please check your spelling and retry.');  // eslint-disable-line max-len
                        this.escapeAndShowMessage(_.template(message)({user: user}));
                    }
                    else if (certificate_invalidation.isValid()) {
                        var self = this;
                        certificate_invalidation.save(null, {
                            wait: true,

                            success: function(model) {
                                self.collection.add(model);
                                message = gettext('Certificate has been successfully invalidated for <%= user %>.');
                                self.escapeAndShowMessage(_.template(message)({user: user}));
                            },

                            error: function(model, response) {
                                try {
                                    var response_data = JSON.parse(response.responseText);
                                    self.escapeAndShowMessage(response_data.message);
                                }
                                catch (exception) {
                                    self.escapeAndShowMessage(
                                        gettext('Server Error, Please refresh the page and try again.')
                                    );
                                }
                            }
                        });
                    }
                    else {
                        this.escapeAndShowMessage(certificate_invalidation.validationError);
                    }
                },

                reValidateCertificate: function(event) {
                    var certificate_invalidation = $(event.target).data();
                    var model = this.collection.get(certificate_invalidation),
                        self = this;

                    if (model) {
                        model.destroy({
                            success: function() {
                                self.escapeAndShowMessage(
                                    gettext('The certificate for this learner has been re-validated and the system is re-running the grade for this learner.')  // eslint-disable-line max-len
                                );
                            },
                            error: function(model, response) {
                                try {
                                    var response_data = JSON.parse(response.responseText);
                                    self.escapeAndShowMessage(response_data.message);
                                }
                                catch (exception) {
                                    self.escapeAndShowMessage(
                                        gettext('Server Error, Please refresh the page and try again.')
                                    );
                                }
                            },
                            wait: true,
                            data: JSON.stringify(model.attributes)
                        });
                    }
                    else {
                        self.escapeAndShowMessage(
                            gettext('Could not find Certificate Invalidation in the list. Please refresh the page and try again')  // eslint-disable-line max-len
                        );
                    }
                },

                isEmailAddress: function validateEmail(email) {
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
