define([
    'jquery',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'support/js/views/certificates'
], function($, AjaxHelpers, CertificatesView) {
    'use strict';

    describe('CertificatesView', function() {

        var view = null,

        REGENERATE_SEARCH_RESULTS = [
            {
                'username': 'student',
                'status': 'notpassing',
                'created': '2015-08-05T17:32:25+00:00',
                'grade': '0.0',
                'type': 'honor',
                'course_key': 'course-v1:edX+DemoX+Demo_Course',
                'download_url': null,
                'modified': '2015-08-06T19:47:07+00:00',
                'regenerate': true
            },
            {
                'username': 'student',
                'status': 'downloadable',
                'created': '2015-08-05T17:53:33+00:00',
                'grade': '1.0',
                'type': 'verified',
                'course_key': 'edx/test/2015',
                'download_url': 'http://www.example.com/certificate.pdf',
                'modified': '2015-08-06T19:47:05+00:00',
                'regenerate': true
            }
        ],

        GENERATE_SEARCH_RESULTS = [
            {
                'username': 'student',
                'status': '',
                'created': '',
                'grade': '',
                'type': '',
                'course_key': 'edx/test1/2016',
                'download_url': null,
                'modified': '',
                'regenerate': false
            }
        ],

        getSearchResults = function() {
            var results = [];

            $('.certificates-results tr').each(function(rowIndex, rowValue) {
                var columns = [];
                $(rowValue).children('td').each(function(colIndex, colValue) {
                    columns[colIndex] = $(colValue).html();
                });

                if (columns.length > 0) {
                    results.push(columns);
                }
            });

            return results;
        },

        searchFor = function(user_filter, course_filter, requests, response) {
            // Enter the search term and submit
            var url = '/certificates/search?user=' + user_filter;
            view.setUserFilter(user_filter);
            if (course_filter) {
                view.setCourseFilter(course_filter);
                url += '&course_id=' + course_filter;
            }
            view.triggerSearch();

            // Simulate a response from the server
            AjaxHelpers.expectJsonRequest(requests, 'GET', url);
            AjaxHelpers.respondWithJson(requests, response);
        },

        regenerateCerts = function(username, courseKey) {
            var sel = '.btn-cert-regenerate[data-course-key="' + courseKey + '"]';
            $(sel).click();
        },

        generateCerts = function(username, courseKey) {
            var sel = '.btn-cert-generate[data-course-key="' + courseKey + '"]';
            $(sel).click();
        };

        beforeEach(function () {
            spyOn(window.history, 'pushState');
            setFixtures('<div class="certificates-content"></div>');
            view = new CertificatesView({
                el: $('.certificates-content')
            }).render();
        });

        it('renders itself', function() {
            expect($('.certificates-search').length).toEqual(1);
            expect($('.certificates-results').length).toEqual(1);
        });

        it('searches for certificates and displays results', function() {
            var requests = AjaxHelpers.requests(this),
                results = [];

            searchFor('student@example.com', '', requests, REGENERATE_SEARCH_RESULTS);
            results = getSearchResults();

            // Expect that the results displayed on the page match the results
            // returned by the server.
            expect(results.length).toEqual(REGENERATE_SEARCH_RESULTS.length);

            // Check the first row of results
            expect(results[0][0]).toEqual(REGENERATE_SEARCH_RESULTS[0].course_key);
            expect(results[0][1]).toEqual(REGENERATE_SEARCH_RESULTS[0].type);
            expect(results[0][2]).toEqual(REGENERATE_SEARCH_RESULTS[0].status);
            expect(results[0][3]).toContain('Not available');
            expect(results[0][4]).toEqual(REGENERATE_SEARCH_RESULTS[0].grade);
            expect(results[0][5]).toEqual(REGENERATE_SEARCH_RESULTS[0].modified);

            // Check the second row of results
            expect(results[1][0]).toEqual(REGENERATE_SEARCH_RESULTS[1].course_key);
            expect(results[1][1]).toEqual(REGENERATE_SEARCH_RESULTS[1].type);
            expect(results[1][2]).toEqual(REGENERATE_SEARCH_RESULTS[1].status);
            expect(results[1][3]).toContain(REGENERATE_SEARCH_RESULTS[1].download_url);
            expect(results[1][4]).toEqual(REGENERATE_SEARCH_RESULTS[1].grade);
            expect(results[1][5]).toEqual(REGENERATE_SEARCH_RESULTS[1].modified);


            searchFor('student@example.com', 'edx/test1/2016', requests, GENERATE_SEARCH_RESULTS);
            results = getSearchResults();
            expect(results.length).toEqual(GENERATE_SEARCH_RESULTS.length);

            // Check the first row of results
            expect(results[0][0]).toEqual(GENERATE_SEARCH_RESULTS[0].course_key);
            expect(results[0][1]).toEqual(GENERATE_SEARCH_RESULTS[0].type);
            expect(results[0][2]).toEqual(GENERATE_SEARCH_RESULTS[0].status);
            expect(results[0][3]).toContain('Not available');
            expect(results[0][4]).toEqual(GENERATE_SEARCH_RESULTS[0].grade);
            expect(results[0][5]).toEqual(GENERATE_SEARCH_RESULTS[0].modified);

        });

        it('searches for certificates and displays a message when there are no results', function() {
            var requests = AjaxHelpers.requests(this),
                results = [];

            searchFor('student@example.com', '', requests, []);
            results = getSearchResults();

            // Expect that no results are found
            expect(results.length).toEqual(0);

            // Expect a message saying there are no results
            expect($('.certificates-results').text()).toContain('No results');
        });

        it('automatically searches for an initial filter if one is provided', function() {
            var requests = AjaxHelpers.requests(this),
                results = [];

            // Re-render the view, this time providing an initial filter.
            view = new CertificatesView({
                el: $('.certificates-content'),
                userFilter: 'student@example.com'
            }).render();

            // Simulate a response from the server
            AjaxHelpers.expectJsonRequest(requests, 'GET', '/certificates/search?user=student@example.com');
            AjaxHelpers.respondWithJson(requests, REGENERATE_SEARCH_RESULTS);

            // Check the search results
            results = getSearchResults();
            expect(results.length).toEqual(REGENERATE_SEARCH_RESULTS.length);
        });

        it('regenerates a certificate for a student', function() {
            var requests = AjaxHelpers.requests(this);

            // Trigger a search
            searchFor('student@example.com', '', requests, REGENERATE_SEARCH_RESULTS);

            // Click the button to regenerate certificates for a user
            regenerateCerts('student', 'course-v1:edX+DemoX+Demo_Course');

            // Expect a request to the server
            AjaxHelpers.expectPostRequest(
                requests,
                '/certificates/regenerate',
                $.param({
                    username: 'student',
                    course_key: 'course-v1:edX+DemoX+Demo_Course'
                })
            );

            // Respond with success
            AjaxHelpers.respondWithJson(requests, '');
        });

         it('generate a certificate for a student', function() {
            var requests = AjaxHelpers.requests(this);

            // Trigger a search
            searchFor('student@example.com', 'edx/test1/2016', requests, GENERATE_SEARCH_RESULTS);

            // Click the button to generate certificates for a user
            generateCerts('student', 'edx/test1/2016');

            // Expect a request to the server
            AjaxHelpers.expectPostRequest(
                requests,
                '/certificates/generate',
                $.param({
                    username: 'student',
                    course_key: 'edx/test1/2016'
                })
            );

            // Respond with success
            AjaxHelpers.respondWithJson(requests, '');
        });

    });
});
