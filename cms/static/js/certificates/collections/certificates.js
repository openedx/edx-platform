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

        IsJsonString: function(str) {
            try {
                JSON.parse(str);
            } catch (e) {
                return false;
            }
            return true;
        },

        //Parse the JSON into Certificate models
        parse: function (certificatesJson) {

            console.log("certificates_collection.parse.start");
            console.log(certificatesJson);

            var modelArray;
            if(this.IsJsonString(certificatesJson)) {
                //Parse the provided JSON and create models in the collection
                modelArray = JSON.parse(certificatesJson);
            } else {
                modelArray = certificatesJson;
            }

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
