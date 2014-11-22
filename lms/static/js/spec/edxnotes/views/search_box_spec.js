define([
    'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/edxnotes/views/search_box',
    'js/edxnotes/collections/notes', 'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function($, _, AjaxHelpers, SearchBoxView, NotesCollection, customMatchers) {
    'use strict';
    describe('EdxNotes SearchBoxView', function() {
        var getSearchBox, submitForm, assertBoxIsEnabled, assertBoxIsDisabled;

        getSearchBox = function (options) {
            options = _.defaults(options || {}, {
                el: $('form.search-box').get(0),
                user: 'test_user',
                courseId: 'test_course_id',
                beforeSearchStart: jasmine.createSpy(),
                search: jasmine.createSpy(),
                error: jasmine.createSpy(),
                complete: jasmine.createSpy()
            });

            return new SearchBoxView(options);
        };

        submitForm = function (searchBox, text) {
            searchBox.$('input').val(text);
            searchBox.$('button[type=submit]').click();
        };

        assertBoxIsEnabled = function (searchBox) {
            expect(searchBox.$el).not.toHaveClass('is-looking');
            expect(searchBox.$('button[type=submit]')).not.toHaveClass('is-disabled');
            expect(searchBox.isDisabled).toBeFalsy();
        };

        assertBoxIsDisabled = function (searchBox) {
            expect(searchBox.$el).toHaveClass('is-looking');
            expect(searchBox.$('button[type=submit]')).toHaveClass('is-disabled');
            expect(searchBox.isDisabled).toBeTruthy();
        };

        beforeEach(function () {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            this.searchBox = getSearchBox();
        });

        it('sends a request with proper information on submit the form', function () {
            var requests = AjaxHelpers.requests(this),
                form = this.searchBox.el,
                request;

            submitForm(this.searchBox, 'test_text');
            request = requests[0];
            expect(request.method).toBe(form.method.toUpperCase());
            expect(request.url).toBe(form.action + '?' + $.param({
                user: 'test_user',
                course_id: 'test_course_id',
                text: 'test_text'
            }));
        });

        it('returns success result', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            expect(this.searchBox.options.beforeSearchStart).toHaveBeenCalledWith(
                'test_text'
            );
            assertBoxIsDisabled(this.searchBox);
            AjaxHelpers.respondWithJson(requests, {
                total: 2,
                rows: [null, null]
            });
            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.search).toHaveBeenCalledWith(
                jasmine.any(NotesCollection), 2, 'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('returns default error message if received data structure is wrong', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            AjaxHelpers.respondWithJson(requests, {});
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('returns default error message if network error occurs', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            AjaxHelpers.respondWithError(requests);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('returns error message if server error occurs', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            assertBoxIsDisabled(this.searchBox);

            requests[0].respond(
                500, {'Content-Type': 'application/json'},
                JSON.stringify({
                    error: 'test error message'
                })
            );

            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'test error message',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('does not send second request during current search', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            assertBoxIsDisabled(this.searchBox);
            submitForm(this.searchBox, 'another_text');
            AjaxHelpers.respondWithJson(requests, {
                total: 2,
                rows: [null, null]
            });
            assertBoxIsEnabled(this.searchBox);
            expect(requests).toHaveLength(1);
        });

        it('returns error message if the field is empty', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, '   ');
            expect(requests).toHaveLength(0);
            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'Search field cannot be blank.',
                '   '
            );
        });
    });
});
