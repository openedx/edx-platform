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
    Collect the XML configuration.
    **/
    collectXmlData: function() {
        var xml = this.codeBox.getValue();
        return {"xml": xml};
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

function SettingsTabView(runtime, element) {
    // initialize settings tab
}
SettingsTabView.collectFieldData = function collectFieldData(element) {
    var $element = $(element);
    var items = $element.find('.settings-list .wrapper-comp-setting');
    var data = {};
    items.each(function (index, item) {
        var $item = $(item);
        var label = $($item.find('label')[0]).data('key');
        var input = $($item.find('input')[0]).val();
        data[label] = input;
    });
    return data;
};
