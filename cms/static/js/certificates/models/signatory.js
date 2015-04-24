define([
    'backbone', 'underscore', 'underscore.string', 'gettext', 'backbone-relational'
],
function(Backbone, _, str, gettext) {
    'use strict';
    console.log('certificate_relational_model.Signatory.start');
    _.str = str;

    var Signatory = Backbone.RelationalModel.extend({
        idAttribute: "id",
        urlRoot: '/api/',
        defaults: {
            name: 'Instructor name',
            title: 'Instructor title'
        },

        initialize: function(attributes, options) {
            console.log('certificate_signatory_model.initialize');
            this.setOriginalAttributes();
            return this;
        },
        parse: function (response) {
            console.log(response.id + " got parse called!");
            return response;
        },

        setOriginalAttributes: function() {
            console.log('certificate_model.setOriginalAttributes');
            this._originalAttributes = this.parse(this.toJSON());
        }
    });

    console.log('certificate_relational_model.Signatory');
    console.log(Signatory)
    return Signatory;
});
