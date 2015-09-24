define(['sinon', 'underscore', 'URI'], function(sinon, _, URI) {
    'use strict';

    var XML_HTTP_READY_STATES, fakeServer, fakeRequests, currentRequest, expectRequest, expectNoRequests,
        expectJsonRequest, expectPostRequest, expectRequestURL, skipResetRequest,
        respondWithJson, respondWithError, respondWithTextError, respondWithNoContent;

    XML_HTTP_READY_STATES = {
        UNSENT: 0,
        OPENED: 1,
        LOADING: 3,
        DONE: 4
    };

    /* These utility methods are used by Jasmine tests to create a mock server or
     * get reference to mock requests. In either case, the cleanup (restore) is done with
     * an after function.
     *
     * This pattern is being used instead of the more common beforeEach/afterEach pattern
     * because we were seeing sporadic failures in the afterEach restore call. The cause of the
     * errors were that one test suite was incorrectly being linked as the parent of an unrelated
     * test suite (causing both suites' afterEach methods to be called). No solution for the root
     * cause has been found, but initializing sinon and cleaning it up on a method-by-method
     * basis seems to work. For more details, see STUD-1264.
     */

    /**
     * Get a reference to the mocked server, and respond
     * to all requests with the specified statusCode.
     */
    fakeServer = function (that, response) {
        var server = sinon.fakeServer.create();
        that.after(function() {
            server.restore();
        });
        server.respondWith(response);
        return server;
    };

    /**
     * Keep track of all requests to a fake server, and
     * return a reference to the Array. This allows tests
     * to respond for individual requests.
     */
    fakeRequests = function (that) {
        var requests = [],
            xhr = sinon.useFakeXMLHttpRequest();
        requests.currentIndex = 0;
        xhr.onCreate = function(request) {
            requests.push(request);
        };

        that.after(function() {
            xhr.restore();
        });
        return requests;
    };

    /**
     * Returns the request that has not yet been responded to. If no such request
     * is available then the current test will fail.
     * @param requests The Sinon requests list.
     * @returns {*} The current request.
     */
    currentRequest = function(requests) {
        expect(requests.length).toBeGreaterThan(requests.currentIndex);
        return requests[requests.currentIndex];
    };

    expectRequest = function(requests, method, url, body) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XML_HTTP_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual(method);
        expect(request.requestBody).toEqual(body);
    };

    /**
     * Verifies the there are no unconsumed requests.
     */
    expectNoRequests = function(requests) {
        expect(requests.length).toEqual(requests.currentIndex);
    };

    expectJsonRequest = function(requests, method, url, jsonRequest) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XML_HTTP_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual(method);
        expect(JSON.parse(request.requestBody)).toEqual(jsonRequest);
    };

    /**
     * Expect that a JSON request be made with the given URL and parameters.
     * @param requests The collected requests
     * @param expectedUrl The expected URL excluding the parameters
     * @param expectedParameters An object representing the URL parameters
     */
    expectRequestURL = function(requests, expectedUrl, expectedParameters) {
        var request = currentRequest(requests),
            parameters;
        expect(new URI(request.url).path()).toEqual(expectedUrl);
        parameters = new URI(request.url).query(true);
        delete parameters._;  // Ignore the cache-busting argument
        expect(parameters).toEqual(expectedParameters);
    };

    /**
     * Intended for use with POST requests using application/x-www-form-urlencoded.
     */
    expectPostRequest = function(requests, url, body) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XML_HTTP_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual("POST");
        expect(_.difference(request.requestBody.split('&'), body.split('&'))).toEqual([]);
    };

    /**
     * Verify that the HTTP request was marked as reset, and then skip it.
     *
     * Note: this is typically used when code has explicitly canceled a request
     * after it has been sent. A good example is when a user chooses to cancel
     * a slow running search.
     */
    skipResetRequest = function(requests) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XML_HTTP_READY_STATES.UNSENT);
        requests.currentIndex++;
    };

    respondWithJson = function(requests, jsonResponse) {
        var request = currentRequest(requests);
        request.respond(200,
            { 'Content-Type': 'application/json' },
            JSON.stringify(jsonResponse));
        requests.currentIndex++;
    };

    respondWithError = function(requests, statusCode, jsonResponse) {
        var request = currentRequest(requests);
        if (_.isUndefined(statusCode)) {
            statusCode = 500;
        }
        if (_.isUndefined(jsonResponse)) {
            jsonResponse = {};
        }
        request.respond(
            statusCode,
            { 'Content-Type': 'application/json' },
            JSON.stringify(jsonResponse)
        );
        requests.currentIndex++;
    };

    respondWithTextError = function(requests, statusCode, textResponse) {
        var request = currentRequest(requests);
        if (_.isUndefined(statusCode)) {
            statusCode = 500;
        }
        if (_.isUndefined(textResponse)) {
            textResponse = "";
        }
        request.respond(
            statusCode,
            { 'Content-Type': 'text/plain' },
            textResponse
        );
        requests.currentIndex++;
    };

    respondWithNoContent = function(requests) {
        var request = currentRequest(requests);
        request.respond(
            204,
            { 'Content-Type': 'application/json' }
        );
        requests.currentIndex++;
    };

    return {
        server: fakeServer,
        requests: fakeRequests,
        currentRequest: currentRequest,
        expectRequest: expectRequest,
        expectNoRequests: expectNoRequests,
        expectJsonRequest: expectJsonRequest,
        expectPostRequest: expectPostRequest,
        expectRequestURL: expectRequestURL,
        skipResetRequest: skipResetRequest,
        respondWithJson: respondWithJson,
        respondWithError: respondWithError,
        respondWithTextError: respondWithTextError,
        respondWithNoContent: respondWithNoContent
    };
});
