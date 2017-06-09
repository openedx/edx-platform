define([
    'backbone'
],
    function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            defaults: {
                username: '',
                lmsBaseUrl: '',
                programsApiUrl: '',
                authUrl: '/programs/id_token/',
                idToken: ''
            }
        });
    }
);
