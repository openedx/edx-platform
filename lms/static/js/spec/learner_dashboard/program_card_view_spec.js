define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/program_card_view',
        'js/learner_dashboard/models/program_model'
    ], function (Backbone, $, ProgramCardView, ProgramModel) {
        
        'use strict';
        /*jslint maxlen: 500 */
        
        describe('Program card View', function () {
            var view = null,
                programModel,
                program = {
                    category: 'xseries',
                    display_category: 'XSeries',
                    status: 'active',
                    subtitle: 'program 1',
                    name: 'test program 1',
                    organizations: [
                        {
                            display_name: 'edX',
                            key: 'edx'
                        }
                    ],
                    created: '2016-03-03T19:18:50.061136Z',
                    modified: '2016-03-25T13:45:21.220732Z',
                    marketing_slug: 'p_2?param=haha&test=b', 
                    id: 146,
                    marketing_url: 'http://www.edx.org/xseries/p_2?param=haha&test=b',
                    banner_image_urls: {
                        w348h116: 'http://www.edx.org/images/test1',
                        w435h145: 'http://www.edx.org/images/test2',
                        w726h242: 'http://www.edx.org/images/test3'
                    }
                };

            beforeEach(function() {
                setFixtures('<div class="program-card"></div>');
                programModel = new ProgramModel(program);
                view = new ProgramCardView({
                    model: programModel
                });
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should load the program-cards based on passed in context', function() {
                var $cards = view.$el;
                expect($cards).toBeDefined();
                expect($cards.find('.title').html().trim()).toEqual(program.name);
                expect($cards.find('.category span').html().trim()).toEqual('XSeries Program');
                expect($cards.find('.organization').html().trim()).toEqual(program.organizations[0].display_name);
                expect($cards.find('.card-link').attr('href')).toEqual(program.marketing_url);
            });

            it('should call reEvaluatePicture if reLoadBannerImage is called', function(){
                spyOn(view, 'reEvaluatePicture');
                view.reLoadBannerImage();
                expect(view.reEvaluatePicture).toHaveBeenCalled();
            });

            it('should handle exceptions from reEvaluatePicture', function(){
                spyOn(view, 'reEvaluatePicture').andCallFake(function(){
                    throw {name:'Picturefill had exceptions'};
                });
                view.reLoadBannerImage();
                expect(view.reEvaluatePicture).toHaveBeenCalled();
                expect(view.reLoadBannerImage).not.toThrow('Picturefill had exceptions');

            });
        });
    }
);
