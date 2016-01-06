// Backbone Application View: CertificateInvalidationView
/*global define, RequireJS */

;(function(define) {
    'use strict';
    define(
        ['jquery', 'underscore', 'gettext', 'backbone', 'js/certificates/models/certificate_invalidation'],

        function($, _, gettext, Backbone, CertificateInvalidationModel) {
            return Backbone.View.extend({
                el: "#certificate-invalidation",
                messages: "div.message",
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
                    var templateSelector = "#" + name + "-tpl",
                    templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                invalidateCertificate: function() {
                    var user = this.$("#certificate-invalidation-user").val();
                    var notes = this.$("#certificate-invalidation-notes").val();

                    var certificate_invalidation = new CertificateInvalidationModel({
                        url: this.collection.url,
                        user: user,
                        notes: notes
                    });

                    if (this.collection.findWhere({user: user})) {
                        this.showMessage(
                            gettext("Certificate of ") + user +
                            gettext(" has already been invalidated. Please check your spelling and retry."
                            ));
                    }
                    else if (certificate_invalidation.isValid()) {
                        var self = this;
                        certificate_invalidation.save(null, {
                            wait: true,

                            success: function(model) {
                                self.collection.add(model);
                                self.showMessage(
                                    gettext('Certificate has been successfully invalidated for ') + user + '.'
                                );
                            },

                            error: function(model, response) {
                                try {
                                    var response_data = JSON.parse(response.responseText);
                                    self.showMessage(response_data.message);
                                }
                                catch(exception) {
                                    self.showMessage(gettext("Server Error, Please refresh the page and try again."));
                                }
                            }
                        });

                    }
                    else {
                        this.showMessage(certificate_invalidation.validationError);
                    }
                },

                reValidateCertificate: function(event) {
                    var certificate_invalidation = $(event.target).data();
                    var model = this.collection.get(certificate_invalidation),
                        self = this;

                    if (model) {
                        model.destroy({
                            success: function() {
                                self.showMessage(gettext('The certificate for this learner has been re-validated and ' +
                                    'the system is re-running the grade for this learner.'));
                            },
                            error: function(model, response) {
                                try {
                                    var response_data = JSON.parse(response.responseText);
                                    self.showMessage(response_data.message);
                                }
                                catch(exception) {
                                    self.showMessage(gettext("Server Error, Please refresh the page and try again."));
                                }
                            },
                            wait: true,
                            data: JSON.stringify(model.attributes)
                        });
                    }
                    else {
                        self.showMessage(gettext('Could not find Certificate Invalidation in the list. ' +
                            'Please refresh the page and try again'));
                    }
                },

                isEmailAddress: function validateEmail(email) {
                    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                    return re.test(email);
                },

                showMessage: function(message) {
                    $(this.messages +  ">p" ).remove();
                    this.$(this.messages).removeClass('hidden').append("<p>"+ gettext(message) + "</p>");
                }

            });
        }
    );
}).call(this, define || RequireJS.define);