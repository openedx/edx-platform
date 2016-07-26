define([
        'js/programs/models/api_config_model'
    ],
    function( ApiConfigModel ) {
        'use strict';

        /**
         * This js module implements the Singleton pattern for an instance
         * of the ApiConfigModel Backbone model.  It returns the same shared
         * instance of that model anywhere it is required.
         */
        var instance;

        if (instance === undefined) {
            instance = new ApiConfigModel();
        }

        return instance;

    }
);
