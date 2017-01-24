define([
    'js/programs/utils/api_config',
    'js/programs/models/auto_auth_model'
],
    function(apiConfig, AutoAuthModel) {
        'use strict';

        return AutoAuthModel.extend({

            url: function() {
                return apiConfig.get('programsApiUrl') + 'organizations/?page_size=1000';
            }

        });
    }
);
