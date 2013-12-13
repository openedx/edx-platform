define(["sinon"], function(sinon) {
    var fakeServer = function (statusCode, that) {
        var server = sinon.fakeServer.create();
        that.after(function() {
            server.restore();
        });
        server.respondWith([statusCode, {}, '']);
        return server;
    };

    var fakeRequests = function (that) {
        var requests = [];
        var xhr = sinon.useFakeXMLHttpRequest();
        xhr.onCreate = function(request) {
            requests.push(request)
        };

        that.after(function() {
            xhr.restore();
        });

        return requests;
    };

    return {
        "server": fakeServer,
        "requests": fakeRequests
    };
});
