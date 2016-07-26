define([
        'backbone',
        'jquery',
        'js/programs/models/program_model'
    ],
    function( Backbone, $, ProgramModel ) {
        'use strict';

        return Backbone.Collection.extend({
            model: ProgramModel
        });
    }
);
