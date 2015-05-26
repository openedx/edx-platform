// Backbone.js Application Collection: Certificates

define([
    'backbone',
    'gettext',
    'js/certificates/models/certificate'
],
function(Backbone, gettext, Certificate) {
    'use strict';
    var CertificateCollection = Backbone.Collection.extend({
        model: Certificate,

        initialize: function(attr, options) {
            // Set up the attributes for this collection instance
            this.url = options.certificateUrl;
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

        parse: function (certificatesJson) {
            // Transforms the provided JSON into a Certificates collection
            var modelArray = this.certificate_array(certificatesJson);

            for (var i in modelArray) {
                this.push(modelArray[i]);
            }
            return this.models;
        }
    });
    return CertificateCollection;
});
