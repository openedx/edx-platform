CMS.Models.FileUpload = Backbone.Model.extend({
    defaults: {
        "title": "",
        "message": "",
        "selectedFile": null,
        "uploading": false,
        "uploadedBytes": 0,
        "totalBytes": 0,
        "finished": false,
        "mimeType": "application/pdf",
        "fileType": "PDF"
    },
    // NOTE: validation functions should return non-internationalized error
    // messages. The messages will be passed through gettext in the template.
    validate: function(attrs, options) {
        if(attrs.selectedFile && attrs.selectedFile.type !== this.attributes.mimeType) {
            return {
                message: "Only " + this.attributes.fileType + " files can be uploaded. Please select a file ending in ." + this.attributes.fileType.toLowerCase() + " to upload.",
                attributes: {selectedFile: true}
            };
        }
    }
});
