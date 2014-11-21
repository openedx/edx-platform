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
Returns:
    XBlockAuthoring.StudioView
**/
XBlockAuthoring.StudioView = function(runtime, element) {
    this.runtime = runtime;

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
    return new XBlockAuthoring.StudioView(runtime, element);
}

function SettingsTabViewInit(runtime, element) {
    var view = new SettingsTabView(runtime, element);
    return view;
}

function SettingsTabView(runtime, element) {
    this.runtime = runtime;
    this.element = element;
    var metadataEditor = $(element).find('.metadata_edit');
    var models = [];
    var metadataData = metadataEditor.data('metadata');
    for (var key in metadataData) {
        if (metadataData.hasOwnProperty(key)) {
            models.push(metadataData[key]);
        }
    }
    this.metadataView = new window.MetadataView.Editor({
        el: metadataEditor,
        collection: new window.MetadataCollection(models)
    });
    this.metadataView.render();
}
SettingsTabView.prototype.collectFieldData = function collectFieldData() {
    var data = this.metadataView.getModifiedMetadataValues();
    return data;
};
