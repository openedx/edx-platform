define([
        'backbone',
        'jquery',
        'js/programs/utils/api_config',
        'js/programs/collections/auto_auth_collection',
        'jquery.cookie'
    ],
    function( Backbone, $, apiConfig, AutoAuthCollection ) {
        'use strict';

        return AutoAuthCollection.extend({
            allRuns: [],

            initialize: function(models, options) {
                // Ignore pagination and give me everything
                var orgStr = options.organization.key,
                    queries = '?org=' + orgStr + '&username=' + apiConfig.get('username') + '&page_size=1000';

                this.url = apiConfig.get('lmsBaseUrl') + 'api/courses/v1/courses/' + queries;
            },

            /*
             *  Abridged version of Backbone.Collection.Create that does not
             *  save the updated Collection back to the server
             *  (code based on original function - http://backbonejs.org/docs/backbone.html#section-134)
             */
            create: function(model, options) {
                options = options ? _.clone(options) : {};
                model = this._prepareModel(model, options);

                if (!!model) {
                    this.add(model, options);
                    return model;
                }
            },

            parse: function(data) {
                this.allRuns = data.results;

                // Because pagination is ignored just set results
                return data.results;
            },

            // Adds a run back into the model for selection
            addRun: function(id) {
                var courseRun = _.findWhere( this.allRuns, { id: id });

                this.create(courseRun);
            },

            // Removes a run from the model for selection
            removeRun: function(id) {
                var courseRun = this.where({id: id});

                this.remove(courseRun);
            }
        });
    }
);
