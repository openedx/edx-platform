// Backbone.js Application Collection: Certificates

define([ // jshint ignore:line
    'backbone',
    'gettext',
    'js/certificates/models/certificate'
],
function(Backbone, gettext, Certificate) {
    'use strict';
    var CertificateCollection = Backbone.Collection.extend({
        model: Certificate,

        /**
         * It represents the maximum number of certificates that a user can create. default set to 1.
         */
        maxAllowed: 1,

        initialize: function(attr, options) {
            // Set up the attributes for this collection instance
            this.url = options.certificateUrl;
            this.bind('remove', this.onModelRemoved, this);
            this.bind('add', this.onModelAdd, this);
        },

        certificate_array: function(certificate_info) {
            var return_array;
            try {
                return_array = JSON.parse(certificate_info);
            } catch (ex) {
                // If it didn't parse, and `certificate_info` is an object then return as it is
                // otherwise return empty array
                if (typeof certificate_info === 'object'){
                    return_array = certificate_info;
                }
                else {
                    console.error(
                        interpolate(
                            gettext('Could not parse certificate JSON. %(message)s'), {message: ex.message}, true
                        )
                    );
                    return_array = [];
                }
            }
            return return_array;
        },

        onModelRemoved: function () {
            // remove the certificate web preview UI.
            if(window.certWebPreview && this.length === 0) {
                window.certWebPreview.remove();
            }
            this.toggleAddNewItemButtonState();
        },

        onModelAdd: function () {
            this.toggleAddNewItemButtonState();
        },

        toggleAddNewItemButtonState: function() {
            // user can create a new item e.g certificate; if not exceeded the maxAllowed limit.
            if(this.length >= this.maxAllowed) {
                $(".action-add").addClass('action-add-hidden');
            } else {
                $(".action-add").removeClass('action-add-hidden');
            }
        },

        parse: function (certificatesJson) {
            // Transforms the provided JSON into a Certificates collection
            var modelArray = this.certificate_array(certificatesJson);

            for (var i in modelArray) {
                if (modelArray.hasOwnProperty(i)) {
                    this.push(modelArray[i]);
                }
            }
            return this.models;
        }
    });
    return CertificateCollection;
});
