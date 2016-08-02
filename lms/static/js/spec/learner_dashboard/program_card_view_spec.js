define([
        'backbone',
        'jquery',
        'js/learner_dashboard/collections/program_progress_collection',
        'js/learner_dashboard/models/program_model',
        'js/learner_dashboard/views/program_card_view'
    ], function (Backbone, $, ProgressCollection, ProgramModel, ProgramCardView) {
        
        'use strict';
        /*jslint maxlen: 500 */
        
        describe('Program card View', function () {
            var view = null,
                programModel,
                program = {
                    category: 'FooBar',
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
                    detail_url: 'http://courses.edx.org/dashboard/programs/1/foo',
                    banner_image_urls: {
                        w348h116: 'http://www.edx.org/images/test1',
                        w435h145: 'http://www.edx.org/images/test2',
                        w726h242: 'http://www.edx.org/images/test3'
                    }
                },
                userProgress = [
                    {
                        id: 146,
                        completed: ['courses', 'the', 'user', 'completed'],
                        in_progress: ['in', 'progress'],
                        not_started : ['courses', 'not', 'yet', 'started']
                    },
                    {
                        id: 147,
                        completed: ['Course 1'],
                        in_progress: [],
                        not_started: ['Course 2', 'Course 3', 'Course 4']
                    }
                ],
                progressCollection = new ProgressCollection(),
                cardRenders = function($card) {
                    expect($card).toBeDefined();
                    expect($card.find('.title').html().trim()).toEqual(program.name);
                    expect($card.find('.category span').html().trim()).toEqual(program.category);
                    expect($card.find('.organization').html().trim()).toEqual(program.organizations[0].key);
                    expect($card.find('.card-link').attr('href')).toEqual(program.detail_url);
                };

            beforeEach(function() {
                setFixtures('<div class="program-card"></div>');
                programModel = new ProgramModel(program);
                progressCollection.set(userProgress);
                view = new ProgramCardView({
                    model: programModel,
                    context: {
                        progressCollection: progressCollection
                    }
                });
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should load the program-card based on passed in context', function() {
                cardRenders(view.$el);
            });

            it('should call reEvaluatePicture if reLoadBannerImage is called', function(){
                spyOn(view, 'reEvaluatePicture');
                view.reLoadBannerImage();
                expect(view.reEvaluatePicture).toHaveBeenCalled();
            });

            it('should handle exceptions from reEvaluatePicture', function(){
                spyOn(view, 'reEvaluatePicture').and.callFake(function(){
                    throw {name:'Picturefill had exceptions'};
                });
                view.reLoadBannerImage();
                expect(view.reEvaluatePicture).toHaveBeenCalled();
                expect(view.reLoadBannerImage).not.toThrow('Picturefill had exceptions');

            });

            it('should calculate the correct percentages for progress bars', function() {
                expect(view.$('.complete').css('width')).toEqual('40%');
                expect(view.$('.in-progress').css('width')).toEqual('20%');
            });

            it('should display the correct completed courses message', function() {
                var program = _.findWhere(userProgress, {id: 146}),
                    completed = program.completed.length,
                    total = completed + program.in_progress.length + program.not_started.length;

                expect(view.$('.certificate-status .status-text').not('.secondary').html()).toEqual('You have earned certificates in ' + completed + ' of the ' + total + ' courses so far.');
            });

            it('should render cards if there is no progressData', function() {
                view.remove();
                view = new ProgramCardView({
                    model: programModel,
                    context: {}
                });
                cardRenders(view.$el);
                expect(view.$('.progress').length).toEqual(0);
            });
        });
    }
);
