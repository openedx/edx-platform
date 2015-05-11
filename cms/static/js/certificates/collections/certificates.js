// Backbone.js Application Collection: Certificates

define([
    'backbone', 'js/certificates/models/certificate'
],
function(Backbone, Certificate) {
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
            } catch (e) {
                return_array = certificate_info;
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
