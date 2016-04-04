define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/program_card_view',
        'js/learner_dashboard/collections/program_collection',
        'js/learner_dashboard/views/collection_list_view'
    ], function (Backbone, $, ProgramCardView, ProgramCollection, CollectionListView) {
        
        'use strict';
        /*jslint maxlen: 500 */
        
        describe('Collection List View', function () {
            var view = null,
                programCollection,
                context = {
                    programsData:[
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
                            marketing_url: 'http://www.edx.org/xseries/p_2?param=haha&test=b'
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
                            marketing_url: 'http://www.edx.org/xseries/gdaf'
                        }
                    ]
                };

            beforeEach(function() {
                setFixtures('<div class="program-cards-container"></div>');
                programCollection = new ProgramCollection(context.programsData);
                view = new CollectionListView({
                    el: '.program-cards-container',
                    childView: ProgramCardView,
                    collection: programCollection
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
                $cards.each(function(index, el){
                    expect($(el).find('.title').html().trim()).toEqual(context.programsData[index].name);
                });
            });

            it('should display no item if collection is empty', function(){
                var $cards;
                view.remove();
                programCollection = new ProgramCollection([]);
                view = new CollectionListView({
                    el: '.program-cards-container',
                    childView: ProgramCardView,
                    collection: programCollection
                });
                view.render();
                $cards = view.$el.find('.program-card');
                expect($cards.length).toBe(0);
            });
        });
    }
);
