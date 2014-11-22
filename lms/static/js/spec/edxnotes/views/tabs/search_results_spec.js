define([
    'jquery', 'js/common_helpers/template_helpers', 'js/common_helpers/ajax_helpers',
    'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs/search_results',
    'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function(
    $, TemplateHelpers, AjaxHelpers, TabsCollection, SearchResultsView, customMatchers
) {
    'use strict';
    describe('EdxNotes SearchResultsView', function() {
        var notes = [
            {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: 'Should be listed first'
            },
            {
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Second added model',
                quote: 'Should be listed second'
            },
            {
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Should be listed third'
            }
        ],
        responseJson = {
            total: 3,
            rows: notes
        },
        getView, submitForm;

        getView = function (tabsCollection, options) {
            options = _.defaults(options || {}, {
                el: $('.edx-notes-page-wrapper'),
                tabsCollection: tabsCollection,
                user: 'test_user',
                courseId: 'course_id',
                createTabOnInitialization: false
            });
            return new SearchResultsView(options);
        };

        submitForm = function (searchBox, text) {
            searchBox.$('input').val(text);
            searchBox.$('button[type=submit]').click();
        };

        beforeEach(function () {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/recent-activity-item', 'templates/edxnotes/tab-item'
            ]);

            this.tabsCollection = new TabsCollection();
        });

        it('does not create a tab and content on initialization', function () {
            var view = getView(this.tabsCollection);
            expect(this.tabsCollection).toHaveLength(0);
            expect(view.$('#edx-notes-page-search-results')).not.toExist();
        });

        it('displays a tab and content on search with proper data and order', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'econd');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(this.tabsCollection).toHaveLength(1);
            expect(this.tabsCollection.at(0).attributes).toEqual({
                name: 'Search Results',
                class_name: 'tab-search-results',
                is_active: true,
                is_closable: true
            });
            expect(view.$('#edx-notes-page-search-results')).toExist();
            expect(view.$('.edx-notes-item-text').eq(1)).toContainHtml(
                '<span class="edx-notes-highlight">econd</span>'
            );
            expect(view.$('.edx-notes-item-quote .edx-notes-highlight')).not.toExist();
            expect(view.$('.edx-notes-page-item')).toHaveLength(3);
            view.searchResults.collection.each(function (model, index) {
                expect(model.get('text')).toBe(notes[index].text);
            });
        });

        it('displays loading indicator when search is running', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test query');
            expect(view.$('.ui-loading')).not.toHaveClass('is-hidden');
            expect(this.tabsCollection).toHaveLength(1);
            expect(view.searchResults).toBeNull();
            expect(view.$('.edx-notes-page-items-list')).not.toExist();
            AjaxHelpers.respondWithJson(requests, responseJson);
            expect(view.$('.ui-loading')).toHaveClass('is-hidden');
        });

        it('displays no results message', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'some text');
            AjaxHelpers.respondWithJson(requests, {
                total: 0,
                rows: []
            });

            expect(view.$('#edx-notes-page-search-results')).not.toExist();
            expect(view.$('#edx-notes-page-no-search-results')).toExist();
            expect(view.$('.edx-notes-highlight')).not.toExist();
            expect(view.$('#edx-notes-page-no-search-results')).toContainText(
                'No results found for "some text".'
            );
        });

        it('does not send an additional request on switching between tabs', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(requests).toHaveLength(1);

            this.tabsCollection.add({});
            this.tabsCollection.at(1).activate();
            expect(view.$('#edx-notes-page-search-results')).not.toExist();
            this.tabsCollection.at(0).activate();

            expect(requests).toHaveLength(1);
            expect(view.$('#edx-notes-page-search-results')).toExist();
            expect(view.$('.edx-notes-page-item')).toHaveLength(3);
        });

        it('can clear search results if tab is closed', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);
            expect(view.searchResults).toBeDefined();
            this.tabsCollection.at(0).destroy();
            expect(view.searchResults).toBeNull();
        });

        it('can correctly show/hide error messages', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test error');
            requests[0].respond(
                500, {'Content-Type': 'application/json'},
                JSON.stringify({
                    error: 'test error message'
                })
            );

            expect(view.$('.inline-error')).not.toHaveClass('is-hidden');
            expect(view.$('.inline-error')).toContainText('test error message');
            expect(view.$('.edx-notes-highlight')).not.toExist();
            expect(view.$('.ui-loading')).toHaveClass('is-hidden');

            submitForm(view.searchBox, 'Second');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(view.$('.inline-error')).toHaveClass('is-hidden');
            expect(view.$('.inline-error')).toBeEmpty();
            expect(view.$('.edx-notes-highlight')).toExist();
        });

        it('can correctly update search results', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this),
                newNotes = [{
                    created: 'December 11, 2014 at 11:10AM',
                    updated: 'December 11, 2014 at 11:10AM',
                    text: 'New Note',
                    quote: 'New Note'
                }];

            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(view.$('.edx-notes-page-item')).toHaveLength(3);

            submitForm(view.searchBox, 'new_test_query');
            AjaxHelpers.respondWithJson(requests, {
                total: 1,
                rows: newNotes
            });

            expect(view.$('.edx-notes-page-item').length).toHaveLength(1);
            view.searchResults.collection.each(function (model, index) {
                expect(model.get('text')).toBe(newNotes[index].text);
            });
        });
    });
});
