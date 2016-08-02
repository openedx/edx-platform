define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/certificate_view'
    ], function (Backbone, $, CertificateView) {
        
        'use strict';
        describe('Certificate View', function () {
            var view = null,
                data = {
                    context: {
                        certificatesData: [
                            {
                                "display_name": "Testing",
                                "credential_url": "https://credentials.stage.edx.org/credentials/dummy-uuid-1/"
                            },
                            {
                                "display_name": "Testing2",
                                "credential_url": "https://credentials.stage.edx.org/credentials/dummy-uuid-2/"
                            }
                        ],
                        sampleCertImageSrc: "/images/programs/sample-cert.png"
                    }
                };

            beforeEach(function() {
                setFixtures('<div class="certificates-list"></div>');
                view = new CertificateView(data);
                view.render();
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should load the certificates based on passed in certificates list', function() {
                var $certificates = view.$el.find('.certificate-link');
                expect($certificates.length).toBe(2);

                $certificates.each(function(index, el){
                    expect($(el).html().trim()).toEqual(data.context.certificatesData[index].display_name);
                    expect($(el).attr('href')).toEqual(data.context.certificatesData[index].credential_url);
                });
                expect(view.$el.find('.hd-6').html().trim()).toEqual('Program Certificates');
                expect(view.$el.find('img').attr('src')).toEqual(data.context.sampleCertImageSrc);
            });

             it('should display no certificate box if certificates list is empty', function() {
                view.remove();
                setFixtures('<div class="certificates-list"></div>');
                view = new CertificateView({
                    context: {certificatesData: []}
                });
                view.render();
                expect(view.$('.certificates-list').length).toBe(0);
            });
        });
    }
);
