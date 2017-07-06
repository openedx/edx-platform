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
                    xseriesUrl: 'http://www.edx.org/xseries',
                    certificatesData: [
                        {
                            "display_name": "Testing",
                            "credential_url": "https://credentials.stage.edx.org/credentials/dummy-uuid-1/"
                        }
                    ],
                    xseriesImage: '/image/test.png'
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

            it('should load the xseries advertising based on passed in xseries URL', function() {
                var $sidebar = view.$el;
                expect($sidebar.find('.program-advertise .advertise-message').html().trim())
                    .toEqual('Browse recently launched courses and see what\'s new in your favorite subjects');
                expect($sidebar.find('.program-advertise .ad-link a').attr('href')).toEqual(context.xseriesUrl);
            });

            it('should load the certificates based on passed in certificates list', function() {
                expect(view.$('.certificate-link').length).toBe(1);
            });

            it('should not load the xseries advertising if no xseriesUrl passed in', function(){
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
