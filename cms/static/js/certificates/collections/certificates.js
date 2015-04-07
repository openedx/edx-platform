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

        IsJsonString: function(str) {
            // Validates the format of the provided string
            try {
                JSON.parse(str);
            } catch (e) {
                return false;
            }
            return true;
        },

        parse: function (certificatesJson) {
            // Transforms the provided JSON into a Certificates collection
            var modelArray;
            if(this.IsJsonString(certificatesJson)) {
                modelArray = JSON.parse(certificatesJson);
            } else {
                modelArray = certificatesJson;
            }
            for (var i in modelArray) {
                this.push(modelArray[i]);
            }
            return this.models;
        }
    });
    return CertificateCollection;
});
