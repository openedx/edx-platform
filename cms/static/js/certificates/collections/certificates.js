define([
    'backbone', 'js/certificates/models/certificate'
],
function(Backbone, Certificate) {
    'use strict';
    console.log("certificate_collection.start");
    var CertificateCollection = Backbone.Collection.extend({
        model: Certificate,
        initialize: function(attr, options) {
            this.url = options.certificateUrl;
        },

        //Parse the JSON into Certificate models
        parse: function (certificatesJson) {

            console.log("certificates_collection.parse.start");
            console.log(certificatesJson);

            //Parse the provided JSON and create models in the collection
            var modelArray = JSON.parse(certificatesJson);
            for (var i in modelArray) {
                console.log(modelArray[i]);
                this.push(modelArray[i]);
                console.log('Parsed! ');

            }

            console.log(this.toJSON());

            //return models
            return this.models;

        }


    });
    console.log("certificate_collection.CertificateCollection");
    console.log(CertificateCollection);
    console.log("certificate_collection.return")
    return CertificateCollection;
});
