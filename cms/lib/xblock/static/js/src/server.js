/* JavaScript interface for interacting with server-side XBlock Authoring */

/* Namespace for Studio XBlock Editing */
if (typeof XBlockAuthoring == "undefined" || !XBlockAuthoring) {
    XBlockAuthoring = {};
}


/**
Interface for server-side XBlock handlers.
Args:
    runtime (Runtime): An XBlock runtime instance.
    element (DOM element): The DOM element representing this XBlock.
Returns:
    XBlockAuthoring.Server
**/
XBlockAuthoring.Server = function(runtime, element) {
    this.runtime = runtime;
    this.element = element;
};


XBlockAuthoring.Server.prototype = {

    /**
    Construct the URL for the handler, specific to one instance of the XBlock on the page.
    Args:
        handler (string): The name of the XBlock handler.
    Returns:
        URL (string)
    **/
    url: function(handler) {
        return this.runtime.handlerUrl(this.element, handler);
    },

    /**
    Load the XBlock's XML definition from the server.
    Returns:
        A JQuery promise, which resolves with the XML definition
        and fails with an error message.
    Example:
        server.loadXml().done(
            function(xml) { console.log(xml); }
        ).fail(
            function(err) { console.log(err); }
        );
    **/
    loadXml: function() {
        var url = this.url('xml');
        return $.Deferred(function(defer) {
            $.ajax({
                type: "POST", url: url, data: "\"\""
            }).done(function(data) {
                if (data.success) {
                    defer.resolveWith(this, [data.xml]);
                }
                else {
                    defer.rejectWith(this, [data.msg]);
                }
            }).fail(function(data) {
                defer.rejectWith(this, ['Could not contact server.']);
            });
        }).promise();
    }
};