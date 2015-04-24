define([
    'backbone', 'js/certificates/models/certificate', 'js/certificates/models/signatory'
],
function(Backbone, Certificate, Signatory) {
    'use strict';
    console.log("certificate_collection.start");
    var CertificateCollection = Backbone.Collection.extend({
        model: Certificate,
        url: '/certificates/edX/DemoX/Demo_Course',

        //Parse the JSON into Certificate models
        parse: function (certificatesJson) {

            console.log("certificates_collection.parse.start");
            console.log(certificatesJson);

            //Parse the provided JSON and create models in the collection
            var modelArray = JSON.parse(certificatesJson);
            for (var i in modelArray) {
                console.log(modelArray[i]);
                this.push(modelArray[i], { isParsed: true});
                console.log('Parsed! ');

            }

            console.log(this.toJSON());

            //return models
            return this.models;

        },

        add: function(attributes, options){
            if(options.parse){
                this.parse(attributes);
            }
            else if(!options.isParsed){

               // Each Certificate should have at-least/Min one signatory. so while creating certificate model,
               // populating the signatory in parallel.
               var signatory = new Signatory({certificate: Certificate});
               attributes['signatories'] = signatory;
            }
            Backbone.Collection.prototype.add.call(this, attributes, options);
        }


    });
    console.log("certificate_collection.CertificateCollection");
    console.log(CertificateCollection);
    console.log("certificate_collection.return")
    return CertificateCollection;
});
