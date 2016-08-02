define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/sidebar_view'
    ], function (Backbone, $, SidebarView) {
        
        'use strict';
        /*jslint maxlen: 500 */
        
        describe('Sidebar View', function () {
            var view = null,
                context = {
                    marketingUrl: 'https://www.example.org/programs',
                    certificatesData: [
                        {
                            "display_name": "Testing",
                            "credential_url": "https://credentials.example.com/credentials/uuid/"
                        }
                    ],
                    sampleCertImageSrc: "/images/programs/sample-cert.png"
                };

            beforeEach(function() {
                setFixtures('<div class="sidebar"></div>');
                
                view = new SidebarView({
                    el: '.sidebar',
                    context: context
                });
                view.render();
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should load the exploration panel given a marketing URL', function() {
                var $sidebar = view.$el;
                expect($sidebar.find('.program-advertise .advertise-message').html().trim())
                    .toEqual('Browse recently launched courses and see what\'s new in your favorite subjects');
                expect($sidebar.find('.program-advertise .ad-link a').attr('href')).toEqual(context.marketingUrl);
            });

            it('should load the certificates based on passed in certificates list', function() {
                expect(view.$('.certificate-link').length).toBe(1);
            });

            it('should not load the advertising panel if no marketing URL is provided', function(){
                var $ad;
                view.remove();
                view = new SidebarView({
                    el: '.sidebar',
                    context: {certificatesData: []}
                });
                view.render();
                $ad = view.$el.find('.program-advertise');
                expect($ad.length).toBe(0);
                expect(view.$('.certificate-link').length).toBe(0);
            });

        });
    }
);
