define([
    'backbone',
    'jquery',
    'js/learner_dashboard/views/program_card_view',
    'js/learner_dashboard/collections/program_collection',
    'js/learner_dashboard/views/collection_list_view',
    'js/learner_dashboard/collections/program_progress_collection'
], function(Backbone, $, ProgramCardView, ProgramCollection, CollectionListView,
        ProgressCollection) {
    'use strict';
        /* jslint maxlen: 500 */

    describe('Collection List View', function() {
        var view = null,
            programCollection,
            progressCollection,
            context = {
                programsData: [
                    {
                        category: 'xseries',
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
                            w348h116: 'http://www.edx.org/images/org1/test1',
                            w435h145: 'http://www.edx.org/images/org1/test2',
                            w726h242: 'http://www.edx.org/images/org1/test3'
                        }
                    },
                    {
                        category: 'xseries',
                        status: 'active',
                        subtitle: 'fda',
                        name: 'fda',
                        organizations: [
                            {
                                display_name: 'edX',
                                key: 'edx'
                            }
                        ],
                        created: '2016-03-09T14:30:41.484848Z',
                        modified: '2016-03-09T14:30:52.840898Z',
                        marketing_slug: 'gdaf',
                        id: 147,
                        marketing_url: 'http://www.edx.org/xseries/gdaf',
                        banner_image_urls: {
                            w348h116: 'http://www.edx.org/images/org2/test1',
                            w435h145: 'http://www.edx.org/images/org2/test2',
                            w726h242: 'http://www.edx.org/images/org2/test3'
                        }
                    }
                ],
                userProgress: [
                    {
                        id: 146,
                        completed: ['courses', 'the', 'user', 'completed'],
                        in_progress: ['in', 'progress'],
                        not_started: ['courses', 'not', 'yet', 'started']
                    },
                    {
                        id: 147,
                        completed: ['Course 1'],
                        in_progress: [],
                        not_started: ['Course 2', 'Course 3', 'Course 4']
                    }
                ]
            };

        beforeEach(function() {
            setFixtures('<div class="program-cards-container"></div>');
            programCollection = new ProgramCollection(context.programsData);
            progressCollection = new ProgressCollection();
            progressCollection.set(context.userProgress);
            context.progressCollection = progressCollection;

            view = new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                collection: programCollection,
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

        it('should load the collection items based on passed in collection', function() {
            var $cards = view.$el.find('.program-card');
            expect($cards.length).toBe(2);
            $cards.each(function(index, el) {
                expect($(el).find('.title').html().trim()).toEqual(context.programsData[index].name);
            });
        });

        it('should display no item if collection is empty', function() {
            var $cards;
            view.remove();
            programCollection = new ProgramCollection([]);
            view = new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                context: {'xseriesUrl': '/programs'},
                collection: programCollection
            });
            view.render();
            $cards = view.$el.find('.program-card');
            expect($cards.length).toBe(0);
        });
        it('should have no title when title not provided', function() {
            var $title;
            setFixtures('<div class="test-container"><div class="program-cards-container"></div></div>');
            view.remove();
            view.render();
            expect(view).toBeDefined();
            $title = view.$el.parent().find('.collection-title');
            expect($title.html()).not.toBeDefined();
        });
        it('should display screen reader header when provided', function() {
            var $title, titleContext = {el: 'h2', title: 'list start'};
            view.remove();
            setFixtures('<div class="test-container"><div class="program-cards-container"></div></div>');
            programCollection = new ProgramCollection(context.programsData);
            view = new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                context: {'xseriesUrl': '/programs'},
                collection: programCollection,
                titleContext: titleContext
            });
            view.render();
            $title = view.$el.parent().find('.collection-title');
            expect($title.html()).toBe(titleContext.title);
        });
    });
}
);
