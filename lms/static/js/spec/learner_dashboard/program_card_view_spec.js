define([
    'backbone',
    'underscore',
    'jquery',
    'js/learner_dashboard/collections/program_progress_collection',
    'js/learner_dashboard/models/program_model',
    'js/learner_dashboard/views/program_card_view'
], function(Backbone, _, $, ProgressCollection, ProgramModel, ProgramCardView) {
    'use strict';
    /* jslint maxlen: 500 */

    describe('Program card View', function() {
        var view = null,
            programModel,
            program = {
                uuid: 'a87e5eac-3c93-45a1-a8e1-4c79ca8401c8',
                title: 'Food Security and Sustainability',
                subtitle: 'Learn how to feed all people in the world in a sustainable way.',
                type: 'XSeries',
                detail_url: 'https://www.edx.org/foo/bar',
                banner_image: {
                    medium: {
                        height: 242,
                        width: 726,
                        url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.medium.jpg'
                    },
                    'x-small': {
                        height: 116,
                        width: 348,
                        url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.x-small.jpg'
                    },
                    small: {
                        height: 145,
                        width: 435,
                        url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.small.jpg'
                    },
                    large: {
                        height: 480,
                        width: 1440,
                        url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.large.jpg'
                    }
                },
                authoring_organizations: [
                    {
                        uuid: '0c6e5fa2-96e8-40b2-9ebe-c8b0df2a3b22',
                        key: 'WageningenX',
                        name: 'Wageningen University & Research'
                    }
                ]
            },
            userProgress = [
                {
                    uuid: 'a87e5eac-3c93-45a1-a8e1-4c79ca8401c8',
                    completed: 4,
                    in_progress: 2,
                    not_started: 4
                },
                {
                    uuid: '91d144d2-1bb1-4afe-90df-d5cff63fa6e2',
                    completed: 1,
                    in_progress: 0,
                    not_started: 3
                }
            ],
            progressCollection = new ProgressCollection(),
            cardRenders = function($card) {
                expect($card).toBeDefined();
                expect($card.find('.title').html().trim()).toEqual(program.title);
                expect($card.find('.category span').html().trim()).toEqual(program.type);
                expect($card.find('.organization').html().trim()).toEqual(program.authoring_organizations[0].key);
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

        it('should call reEvaluatePicture if reLoadBannerImage is called', function() {
            spyOn(view, 'reEvaluatePicture');
            view.reLoadBannerImage();
            expect(view.reEvaluatePicture).toHaveBeenCalled();
        });

        it('should handle exceptions from reEvaluatePicture', function() {
            var message = 'Picturefill had exceptions';

            spyOn(view, 'reEvaluatePicture').and.callFake(function() {
                var error = {name: message};

                throw error;
            });
            view.reLoadBannerImage();
            expect(view.reEvaluatePicture).toHaveBeenCalled();
            expect(view.reLoadBannerImage).not.toThrow(message);
        });

        it('should show the right number of progress bar segments', function() {
            expect(view.$('.progress-bar .completed').length).toEqual(4);
            expect(view.$('.progress-bar .enrolled').length).toEqual(2);
        });

        it('should display the correct course status numbers', function() {
            expect(view.$('.number-circle').text()).toEqual('424');
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
