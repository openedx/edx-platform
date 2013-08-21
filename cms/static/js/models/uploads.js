CMS.Models.FileUpload = Backbone.Model.extend({
    defaults: {
        "title": "",
        "message": "",
        "selectedFile": null,
        "uploading": false,
        "uploadedBytes": 0,
        "totalBytes": 0,
        "finished": false,
        "mimeTypes": []
    },
    validate: function(attrs, options) {
        if(attrs.selectedFile && !_.contains(this.attributes.mimeTypes, attrs.selectedFile.type)) {
            return {
                message: _.template(
                    gettext("Only <%= fileTypes %> files can be uploaded. Please select a file ending in <%= fileExtensions %> to upload."),
                    this.formatValidTypes()
                ),
                attributes: {selectedFile: true}
            };
        }
    },
    // Return a list of this uploader's valid file types
    fileTypes: function() {
        return _.map(
            this.attributes.mimeTypes,
            function(type) {
                return type.split('/')[1].toUpperCase();
            }
        );
    },
    // Return strings for the valid file types and extensions this
    // uploader accepts, formatted as natural language
    formatValidTypes: function() {
        if(this.attributes.mimeTypes.length === 1) {
            return {
                fileTypes: this.fileTypes()[0],
                fileExtensions: '.' + this.fileTypes()[0].toLowerCase()
            };
        }
        var or = gettext('or');
        var formatTypes = function(types) {
            return _.template('<%= initial %> <%= or %> <%= last %>', {
                initial: _.initial(types).join(', '),
                or: or,
                last: _.last(types)
            });
        };
        return {
            fileTypes: formatTypes(this.fileTypes()),
            fileExtensions: formatTypes(
                _.map(this.fileTypes(),
                      function(type) {
                          return '.' + type.toLowerCase();
                      })
            )
        };
    }
});
