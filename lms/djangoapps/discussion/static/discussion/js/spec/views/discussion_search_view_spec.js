define([
    'jquery',
    'edx-ui-toolkit/js/utils/constants',
    'discussion/js/views/discussion_search_view'
],
    function($, constants, DiscussionSearchView) {
        'use strict';

        describe('DiscussionSearchView', function() {
            var view;
            beforeEach(function() {
                setFixtures('<div class="search-container"></div>');
                view = new DiscussionSearchView({
                    el: $('.search-container'),
                    threadListView: {
                        performSearch: jasmine.createSpy()
                    }
                }).render();
            });

            describe('Search events', function() {
                it('perform search when enter pressed inside search textfield', function() {
                    view.$el.find('.search-input').trigger($.Event('keydown', {
                        which: constants.keyCodes.enter
                    }));
                    expect(view.threadListView.performSearch).toHaveBeenCalled();
                });

                it('perform search when search icon is clicked', function() {
                    view.$el.find('.search-btn').click();
                    expect(view.threadListView.performSearch).toHaveBeenCalled();
                });
            });
        });
    }
);
