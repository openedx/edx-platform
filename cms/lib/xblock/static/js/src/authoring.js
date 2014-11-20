/* JavaScript for Studio editing view of XBlock XML */


/* Namespace for Studio XBlock Editing */
if (typeof XBlockAuthoring == "undefined" || !XBlockAuthoring) {
    XBlockAuthoring = {};
}


/**
Interface for editing view in Studio.
The constructor initializes the DOM for editing.
Args:
    runtime (Runtime): an XBlock runtime instance.
    element (DOM element): The DOM element representing this XBlock.
    server (XBlockAuthoring.Server): The interface to the XBlock server.
Returns:
    XBlockAuthoring.StudioView
**/
XBlockAuthoring.StudioView = function(runtime, element, server) {
    this.runtime = runtime;
    this.server = server;

    // Initialize the code box
    this.codeBox = CodeMirror.fromTextArea(
        $(element).find('.xml-editor').first().get(0),
        {mode: "xml", lineNumbers: true, lineWrapping: true}
    );
};


XBlockAuthoring.StudioView.prototype = {

    /**
    Load the XBlock XML definition from the server and display it in the view.
    **/
    load: function() {
        var view = this;
        this.server.loadXml().done(
            function(xml) {
                view.codeBox.setValue(xml);
            }).fail(function(msg) {
                view.showError(msg);
            }
        );
    },

    /**
    Save the updated XML definition to the server.
    **/
    updateXml: function() {
        // Notify the client-side runtime that we are starting
        // to save so it can show the "Saving..." notification
        this.runtime.notify('save', {state: 'start'});

        // Send the updated XML to the server
        var xml = this.codeBox.getValue();
        var view = this;
        this.server.updateXml(xml).done(function() {
            // Notify the client-side runtime that we finished saving
            // so it can hide the "Saving..." notification.
            view.runtime.notify('save', {state: 'end'});

            // Reload the XML definition in the editor
            view.load();
        }).fail(function(msg) {
            view.showError(msg);
        });
    }
};

/* XBlock entry point for Studio view */
function XBlockXMLEditor(runtime, element) {

    /**
    Initialize the editing interface on page load.
    **/
    $(function($) {
        var server = new XBlockAuthoring.Server(runtime, element);
        var view = new XBlockAuthoring.StudioView(runtime, element, server);
        view.load();
    });
}