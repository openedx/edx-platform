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
    Collect the XML configuration.
    **/
    collectXmlData: function() {
        return this.codeBox.getValue();
    }
};

/* XBlock entry point for Studio view */
function XBlockXMLEditor(runtime, element) {

    /**
    Initialize the editing interface on page load.
    **/
    var server = new XBlockAuthoring.Server(runtime, element);
    return new XBlockAuthoring.StudioView(runtime, element, server);
}

function SettingsTabViewInit(runtime, element) {
    var view = new SettingsTabView(runtime, element);
    return view;
}
function SettingsTabView(runtime, element) {
    this.runtime = runtime;
    this.element = element;
    debugger
    require(["js/views/metadata", "js/collections/metadata"],
        function (MetadataView, MetadataCollection) {
            debugger
            var metadataEditor = $(element).find('.metadata_edit');
            var models = [];
            var metadataData = metadataEditor.data('metadata');
            for (var key in metadataData) {
                if (metadataData.hasOwnProperty(key)) {
                    models.push(metadataData[key]);
                }
            }
            var metadataView = new MetadataView.Editor({
                el: metadataEditor,
                collection: new MetadataCollection(models)
            });
            metadataView.render();
        }
    );
}
SettingsTabView.prototype.collectFieldData = function collectFieldData() {
    var $element = $(this.element);
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
