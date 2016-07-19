define([
        'underscore',
        'backbone',
        'jquery',
        'js/programs/utils/api_config',
        'js/programs/models/auto_auth_model'
    ],
    function( _, Backbone, $, apiConfig, AutoAuthModel ) {
        'use strict';

        describe('AutoAuthModel', function () {

            var model,
                testErrorCallback,
                fakeAjaxDeferred,
                spyOnBackboneSync,
                callSync,
                checkAuthAttempted,
                dummyModel = {'dummy': 'model'},
                authUrl = apiConfig.get( 'authUrl' );

            beforeEach( function() {

                // instance under test
                model = new AutoAuthModel();

                // stand-in for the error callback a caller might pass with options to Backbone.Model.sync
                testErrorCallback = jasmine.createSpy();

                fakeAjaxDeferred = $.Deferred();
                spyOn( $, 'ajax' ).and.returnValue( fakeAjaxDeferred );
                return fakeAjaxDeferred;

            });

            spyOnBackboneSync = function( status ) {
                // set up Backbone.sync to invoke its error callback with the desired HTTP status
                spyOn( Backbone, 'sync' ).and.callFake( function(method, model, options) {
                    var fakeXhr = options.xhr = { status: status };
                    options.error(fakeXhr, 0, '');
                });
            };

            callSync = function(options) {
                var params,
                    syncOptions = _.extend( { error: testErrorCallback }, options || {} );

                model.sync('GET', dummyModel, syncOptions);

                // make sure Backbone.sync was called with custom error handling
                expect( Backbone.sync.calls.count() ).toEqual(1);
                params = _.object( ['method', 'model', 'options'], Backbone.sync.calls.mostRecent().args );
                expect( params.method ).toEqual( 'GET' );
                expect( params.model ).toEqual( dummyModel );
                expect( params.options.error ).not.toEqual( testErrorCallback );
                return params;
            };

            checkAuthAttempted = function(isExpected) {
                if (isExpected) {
                    expect( $.ajax ).toHaveBeenCalled();
                    expect( $.ajax.calls.mostRecent().args[0].url ).toEqual( authUrl );
                } else {
                    expect( $.ajax ).not.toHaveBeenCalled();
                }
            };

            it( 'should exist', function () {
                expect( model ).toBeDefined();
            });

            it( 'should intercept 401 errors and attempt auth', function() {

                var callParams;

                spyOnBackboneSync(401);

                callSync();

                // make sure the auth attempt was initiated
                checkAuthAttempted(true);

                // fire the success handler for the fake ajax call, with id token response data
                fakeAjaxDeferred.resolve( {id_token: 'test-id-token'} );

                // make sure the original request was retried with token, and without custom error handling
                expect( Backbone.sync.calls.count() ).toEqual(2);
                callParams = _.object( ['method', 'model', 'options'], Backbone.sync.calls.mostRecent().args );
                expect( callParams.method ).toEqual( 'GET' );
                expect( callParams.model ).toEqual( dummyModel );
                expect( callParams.options.error ).toEqual( testErrorCallback );
                expect( callParams.options.headers.Authorization ).toEqual( 'JWT test-id-token' );

            });

            it( 'should not intercept non-401 errors', function() {

                spyOnBackboneSync(403);

                // invoke AutoAuthModel.sync
                callSync();

                // make sure NO auth attempt was initiated
                checkAuthAttempted(false);

                // make sure the original request was not retried
                expect( Backbone.sync.calls.count() ).toEqual(1);

                // make sure the default error handling was invoked
                expect( testErrorCallback ).toHaveBeenCalled();

            });

        });
    }
);
