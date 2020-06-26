define(['backbone', 'underscore', 'gettext'], function(Backbone, _, gettext) {
    var FileUpload = Backbone.Model.extend({
        defaults: {
            title: '',
            message: '',
            selectedFile: null,
            uploading: false,
            uploadedBytes: 0,
            totalBytes: 0,
            finished: false,
            mimeTypes: [],
            fileFormats: []
        },
        validate: function(attrs, options) {
            if (attrs.selectedFile && !this.checkTypeValidity(attrs.selectedFile)) {
                return {
                    message: _.template(gettext('Only <%- fileTypes %> files can be uploaded. Please select a file ending in <%- (fileExtensions) %> to upload.'))(  // eslint-disable-line max-len
                    this.formatValidTypes()
                ),
                    attributes: {selectedFile: true}
                };
            }
        },
    // Return a list of this uploader's valid file types
        fileTypes: function() {
            var mimeTypes = _.map(
                this.attributes.mimeTypes,
                function(type) {
                    return type.split('/')[1].toUpperCase();
                }
            ),
                fileFormats = _.map(
                this.attributes.fileFormats,
                function(type) {
                    return type.toUpperCase();
                }
            );

            return mimeTypes.concat(fileFormats);
        },
        checkTypeValidity: function(file) {
            var attrs = this.attributes,
                getRegExp = function(formats) {
                // Creates regular expression like: /(?:.+)\.(jpg|png|gif)$/i
                    return RegExp(('(?:.+)\\.(' + formats.join('|') + ')$'), 'i');
                };

            return (attrs.mimeTypes.length === 0 && attrs.fileFormats.length === 0) ||
                _.contains(attrs.mimeTypes, file.type) ||
                getRegExp(attrs.fileFormats).test(file.name);
        },
    // Return strings for the valid file types and extensions this
    // uploader accepts, formatted as natural language
        formatValidTypes: function() {
            var attrs = this.attributes;

            if (attrs.mimeTypes.concat(attrs.fileFormats).length === 1) {
                return {
                    fileTypes: this.fileTypes()[0],
                    fileExtensions: '.' + this.fileTypes()[0].toLowerCase()
                };
            }
            var or = gettext('or');
            var formatTypes = function(types) {
                return _.template('<%- initial %> <%- or %> <%- last %>')({
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

    return FileUpload;
}); // end define()
