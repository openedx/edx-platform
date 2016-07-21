define([
        'backbone',
        'jquery',
        'js/programs/utils/api_config',
        'js/programs/models/auto_auth_model',
        'gettext',
        'jquery.cookie'
    ],
    function( Backbone, $, apiConfig, AutoAuthModel, gettext ) {
        'use strict';

        return AutoAuthModel.extend({

            // Backbone.Validation rules.
            // See: http://thedersen.com/projects/backbone-validation/#configure-validation-rules-on-the-model.
            validation: {
                name: {
                    required: true,
                    maxLength: 255
                },
                subtitle: {
                    // The underlying Django model does not require a subtitle.
                    maxLength: 255
                },
                category: {
                    required: true,
                    oneOf: ['xseries', 'micromasters']
                },
                organizations: 'validateOrganizations',
                marketing_slug: {
                    maxLength: 255
                }
            },

            initialize: function() {
                this.url = apiConfig.get('programsApiUrl') + 'programs/' + this.id + '/';
            },

            validateOrganizations: function( orgArray ) {
                /**
                 * The array passed to this method contains a single object representing
                 * the selected organization; the object contains the organization's key.
                 * In the future, multiple organizations might be associated with a program.
                 */
                var i,
                    len = orgArray ? orgArray.length : 0;

                for ( i = 0; i < len; i++ ) {
                    if ( orgArray[i].key === 'false' ) {
                        return gettext('Please select a valid organization.');
                    }
                }
            },

            getConfig: function( options ) {
                var patch = options && options.patch,
                    params = patch ? this.get('id') + '/' : '',
                    config = _.extend({ validate: true, parse: true }, {
                        type: patch ? 'PATCH' : 'POST',
                        url: apiConfig.get('programsApiUrl') + 'programs/' + params,
                        contentType: patch ? 'application/merge-patch+json' : 'application/json',
                        context: this,
                        // NB: setting context fails in tests
                        success: _.bind( this.saveSuccess, this ),
                        error: _.bind( this.saveError, this )
                    });

                if ( patch ) {
                    config.data = JSON.stringify( options.update ) || this.attributes;
                }

                return config;
            },

            patch: function( data ) {
                this.save({
                    patch: true,
                    update: data
                });
            },

            save: function( options ) {
                var method,
                    patch = options && options.patch ? true : false,
                    config = this.getConfig( options );

                /**
                 * Simplified version of code from the default Backbone save function
                 * http://backbonejs.org/docs/backbone.html#section-87
                 */
                method = this.isNew() ? 'create' : ( patch ? 'patch' : 'update' );

                this.sync( method, this, config );
            },

            saveError: function( jqXHR ) {
                this.trigger( 'error', jqXHR );
            },

            saveSuccess: function( data ) {
                this.set({ id: data.id });
                this.trigger( 'sync', this );
            }
        });
    }
);
