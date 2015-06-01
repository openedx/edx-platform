// Backbone.js Application Model: Certificate Signatory

define([ // jshint ignore:line
    'underscore',
    'underscore.string',
    'backbone',
    'backbone-relational',
    'gettext'
],
function(_, str, Backbone, BackboneRelational, gettext) {
    'use strict';
    _.str = str;

    var Signatory = Backbone.RelationalModel.extend({
        idAttribute: "id",
        defaults: {
            name: 'Name of the signatory',
            title: 'Title of the signatory',
            organization: 'Organization of the signatory',
            signature_image_path: ''
        },

        initialize: function() {
            // Set up the initial state of the attributes set for this model instance
            this.setOriginalAttributes();
            return this;
        },

        parse: function (response) {
            // Parse must be defined for the model, but does not need to do anything special right now
            return response;
        },

        validate: function(attrs) {
            var errors = null;
            if(_.has(attrs, 'name') && attrs.name.length > 40) {
                errors = _.extend({
                    'name': gettext('Signatory name should not be more than 40 characters long.')
                }, errors);
            }
            if(_.has(attrs, 'title')){
                var title = attrs.title;
                var lines = title.split(/\r\n|\r|\n/);
                if (lines.length > 2) {
                    errors = _.extend({
                        'title': gettext('Signatory title should span over maximum of 2 lines.')
                    }, errors);
                }
                else if ((lines.length > 1 && (lines[0].length > 40 || lines[1].length > 40)) ||
                    (lines.length === 1 && title.length > 40)) {
                    errors = _.extend({
                        'title': gettext('Signatory title should have maximum of 40 characters per line.')
                    }, errors);
                }

            }
            if(_.has(attrs, 'organization') && attrs.organization.length > 40) {
                errors = _.extend({
                    'organization': gettext('Signatory organization should not be more than 40 characters long.')
                }, errors);
            }
            if (errors !== null){
                return errors;
            }

        },

        setOriginalAttributes: function() {
            // Remember the current state of this model (enables edit->cancel use cases)
            this._originalAttributes = this.parse(this.toJSON());
        }
    });
    return Signatory;
});
