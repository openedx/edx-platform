/**
 * These utility methods are used by Jasmine tests to create a mock server or
 * get reference to mock requests. In either case, the cleanup (restore) is done with
 * an after function.
 *
 * This pattern is being used instead of the more common beforeEach/afterEach pattern
 * because we were seeing sporadic failures in the afterEach restore call. The cause of the
 * errors were that one test suite was incorrectly being linked as the parent of an unrelated
 * test suite (causing both suites' afterEach methods to be called). No solution for the root
 * cause has been found, but initializing sinon and cleaning it up on a method-by-method
 * basis seems to work. For more details, see STUD-1264.
 *
 * @module AjaxHelpers
 */
define(['sinon', 'underscore', 'URI'], function(sinon, _, URI) {
    'use strict';

    var XHR_READY_STATES, fakeServer, createFakeRequests, withFakeRequests, fakeRequests, currentRequest,
        expectRequest, expectNoRequests, expectJsonRequest, expectPostRequest, expectRequestURL, skipResetRequest,
        respond, respondWithJson, respondWithError, respondWithTextError, respondWithNoContent;

    /**
     * An enumeration of valid XHR ready states.
     */
    XHR_READY_STATES = {
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
     * Get a reference to the mocked server, and respond to all requests
     * with the specified response.
     *
     * @param {string} response the fake response.
     * @returns {*} The current request.
     */
    fakeServer = function(response) {
        var server = sinon.fakeServer.create();
        afterEach(function() {
            if (server) {
                server.restore();
            }
        });
        server.respondWith(response);
        return server;
    };

    createFakeRequests = function() {
        var requests = [],
            xhr = sinon.useFakeXMLHttpRequest();

        requests.currentIndex = 0;
        requests.restore = function() {
            if (xhr && 'restore' in xhr) {
                xhr.restore();
            }
        };
        xhr.onCreate = function(request) {
            requests.push(request);
        };

        return requests;
    };

    /**
     * Keep track of all requests to a fake server, and return a reference to the Array.
     * This allows tests to respond to individual requests.
     *
     * @returns {Array} An array tracking the fake requests.
     */
    fakeRequests = function() {
        var requests = createFakeRequests();
        afterEach(function() {
            requests.restore();
        });
        return requests;
    };

    /**
     * Wraps a test function so that it is invoked with an additional parameter
     * containing an array of fake HTTP requests.
     *
     * @param {function} test A function to be invoked with the fake requests.
     * @returns {function} A wrapped version of the input function.
     */
    withFakeRequests = function(test) {
        return function() {
            var requests = createFakeRequests(),
                args = Array.prototype.slice.call(arguments);
            test.apply(null, args.concat([requests]));
            requests.restore();
        };
    };

    /**
     * Returns the request that has not yet been responded to. If no such request
     * is available then the current test will fail.
     *
     * @param {object} requests an array of fired sinon requests
     * @returns {*} The current request.
     */
    currentRequest = function(requests) {
        expect(requests.length).toBeGreaterThan(requests.currentIndex);
        return requests[requests.currentIndex];
    };

    /**
     * Expect that a request was made as expected.
     *
     * @param {object} requests an array of fired sinon requests
     * @param {string} method the expected method of the request
     * @param {string} url the expected url of the request
     * @param {string} body the expected request body
     */
    expectRequest = function(requests, method, url, body) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XHR_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual(method);
        if (typeof body === 'undefined') {
            // The body of the request may not be germane to the current test,
            // such as a call by a library, so allow it to be ignored.
            return;
        }
        expect(request.requestBody).toEqual(body);
    };

    /**
     * Verifies that there are no unconsumed requests.
     *
     * @param {object} requests an array of fired sinon requests
     */
    expectNoRequests = function(requests) {
        expect(requests.length).toEqual(requests.currentIndex);
    };

    /**
     * Expect that a request with a JSON payload was made as expected.
     *
     * @param {object} requests an array of fired sinon requests
     * @param {string} method the expected method of the request
     * @param {string} url the expected url of the request
     * @param {object} jsonRequest the expected request body as an object
     */
    expectJsonRequest = function(requests, method, url, jsonRequest) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XHR_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual(method);
        expect(JSON.parse(request.requestBody)).toEqual(jsonRequest === undefined ? null : jsonRequest);
    };

    /**
     * Expect that a JSON request be made with the given URL and parameters.
     *
     * @param {object} requests The collected requests
     * @param {string} expectedUrl The expected URL excluding the parameters
     * @param {object} expectedParameters An object representing the URL parameters
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
     *
     * @param {object} requests an array of fired sinon requests
     * @param {string} url the expected url of the request
     * @param {string} body the expected body of the request
     */
    expectPostRequest = function(requests, url, body) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XHR_READY_STATES.OPENED);
        expect(request.url).toEqual(url);
        expect(request.method).toEqual('POST');
        expect(_.difference(request.requestBody.split('&'), body.split('&'))).toEqual([]);
    };

    /**
     * Verify that the HTTP request was marked as reset, and then skip it.
     *
     * Note: this is typically used when code has explicitly canceled a request
     * after it has been sent. A good example is when a user chooses to cancel
     * a slow running search.

     * @param {object} requests an array of fired sinon requests
     */
    skipResetRequest = function(requests) {
        var request = currentRequest(requests);
        expect(request.readyState).toEqual(XHR_READY_STATES.UNSENT);
        // Our ESLint config bans mutating params, but fixing this would require breaking AjaxHelpers API
        requests.currentIndex += 1;  // eslint-disable-line no-param-reassign
    };

    /**
     * Respond to a server request with a set of options:
     *
     *   - `statusCode`: the status code to be returned (defaults to 200)
     *   - `contentType`: the content type of the response (defaults to 'application/json')
     *   - `body`: the body of the response (if JSON, it will be converted to a string)
     *
     * @param {object} requests an array of fired sinon requests
     * @param {object} options the options to provide to the response
     */
    respond = function(requests, options) {
        var request = currentRequest(requests),
            statusCode = options.statusCode || 200,
            contentType = options.contentType || 'application/json',
            body = options.body || '';
        request.respond(statusCode,
            {'Content-Type': contentType},
            contentType === 'application/json' ? JSON.stringify(body || {}) : body
        );
        requests.currentIndex += 1;  // eslint-disable-line no-param-reassign
    };

    /**
     * Respond to a request with JSON.
     *
     * @param {object} requests an array of fired sinon requests
     * @param {object} body an object to be serialized to the response
     */
    respondWithJson = function(requests, body) {
        respond(requests, {
            body: body
        });
    };

    /**
     * Respond to a request with an error status code and a JSON
     * payload.
     *
     * @param {object} requests an array of fired sinon requests
     * @param {int} statusCode the HTTP status code of the response
     *     (defaults to 500)
     * @param {object} body an object to be serialized to the response
     */
    respondWithError = function(requests, statusCode, body) {
        respond(requests, {
            statusCode: statusCode || 500,
            body: body
        });
    };

    /**
     * Respond to a request with an error status code.
     *
     * @param {object} requests an array of fired sinon requests
     * @param {int} statusCode the HTTP status code of the response
     *     (defaults to 500)
     * @param {object} body the response body as a string
     */
    respondWithTextError = function(requests, statusCode, body) {
        respond(requests, {
            statusCode: statusCode || 500,
            contentType: 'text/plain',
            body: body
        });
    };

    /**
     * Respond to a request with an HTTP 204.
     *
     * @param {object} requests an array of fired sinon requests
     */
    respondWithNoContent = function(requests) {
        respond(requests, {
            statusCode: 204
        });
    };

    return {
        server: fakeServer,
        requests: fakeRequests,
        withFakeRequests: withFakeRequests,
        currentRequest: currentRequest,
        expectRequest: expectRequest,
        expectNoRequests: expectNoRequests,
        expectJsonRequest: expectJsonRequest,
        expectPostRequest: expectPostRequest,
        expectRequestURL: expectRequestURL,
        skipResetRequest: skipResetRequest,
        respond: respond,
        respondWithJson: respondWithJson,
        respondWithError: respondWithError,
        respondWithTextError: respondWithTextError,
        respondWithNoContent: respondWithNoContent
    };
});
