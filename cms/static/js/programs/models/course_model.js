define([
        'backbone',
        'jquery',
        'js/programs/utils/api_config',
        'js/programs/models/auto_auth_model',
        'jquery.cookie',
        'gettext'
    ],
    function( Backbone, $, apiConfig, AutoAuthModel ) {
        'use strict';

        return AutoAuthModel.extend({

            validation: {
                key: {
                    required: true,
                    maxLength: 64
                },
                display_name: {
                    required: true,
                    maxLength: 128
                }
            },

            labels: {
                key: gettext('Course Code'),
                display_name: gettext('Course Title')
            },

            defaults: {
                display_name: false,
                key: false,
                organization: [],
                run_modes: []
            }
        });
    }
);
