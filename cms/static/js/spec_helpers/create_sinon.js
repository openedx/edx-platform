define(["sinon", "underscore"], function(sinon, _) {
    var fakeServer, fakeRequests, expectJsonRequest, respondWithJson, respondWithError, respondToDelete;

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
    fakeServer = function (statusCode, that) {
        var server = sinon.fakeServer.create();
        that.after(function() {
            server.restore();
        });
        server.respondWith([statusCode, {}, '']);
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
        xhr.onCreate = function(request) {
            requests.push(request);
        };

        that.after(function() {
            xhr.restore();
        });

        return requests;
    };

    expectJsonRequest = function(requests, method, url, jsonRequest, requestIndex) {
        var request;
        if (_.isUndefined(requestIndex)) {
            requestIndex = requests.length - 1;
        }
        request = requests[requestIndex];
        expect(request.url).toEqual(url);
        expect(request.method).toEqual(method);
        expect(JSON.parse(request.requestBody)).toEqual(jsonRequest);
    };

    respondWithJson = function(requests, jsonResponse, requestIndex) {
        if (_.isUndefined(requestIndex)) {
            requestIndex = requests.length - 1;
        }
        requests[requestIndex].respond(200,
            { "Content-Type": "application/json" },
            JSON.stringify(jsonResponse));
    };

    respondWithError = function(requests, requestIndex) {
        if (_.isUndefined(requestIndex)) {
            requestIndex = requests.length - 1;
        }
        requests[requestIndex].respond(500,
            { "Content-Type": "application/json" },
            JSON.stringify({ }));
    };

    respondToDelete = function(requests, requestIndex) {
        if (_.isUndefined(requestIndex)) {
            requestIndex = requests.length - 1;
        }
        requests[requestIndex].respond(204,
            { "Content-Type": "application/json" });
    };

    return {
        "server": fakeServer,
        "requests": fakeRequests,
        "expectJsonRequest": expectJsonRequest,
        "respondWithJson": respondWithJson,
        "respondWithError": respondWithError,
        "respondToDelete": respondToDelete
    };
});
