define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/template_helpers',
    'common/js/spec_helpers/ajax_helpers',
    'js/verify_student/views/image_input_view',
    'js/verify_student/models/verification_model'
], function( $, Backbone, TemplateHelpers, AjaxHelpers, ImageInputView, VerificationModel ) {
    'use strict';

    describe( 'edx.verify_student.ImageInputView', function() {

        var IMAGE_DATA = 'abcd1234';

        var createView = function() {
            return new ImageInputView({
                el: $( '#current-step-container' ),
                model: new VerificationModel({}),
                modelAttribute: 'faceImage',
                errorModel: new ( Backbone.Model.extend({}) )(),
                submitButton: $( '#submit_button' ),
            }).render();
        };

        var uploadImage = function( view, fileType, callback ) {
            var imageCapturedEvent = false,
                errorEvent = false;

            // Since image upload is an asynchronous process,
            // we need to wait for the upload to complete
            // before checking the outcome.
            runs(function() {
                var fakeFile,
                    fakeEvent = { target: { files: [] } };

                // If no file type is specified, don't add any files.
                // This simulates what happens when the user clicks
                // "cancel" after clicking the input.
                if ( fileType !== null) {
                    fakeFile = new Blob(
                        [ IMAGE_DATA ],
                        { type: 'image/' + fileType }
                    );
                    fakeEvent.target.files = [ fakeFile ];
                }

                // Wait for either a successful upload or an error
                view.on( 'imageCaptured', function() {
                    imageCapturedEvent = true;
                });
                view.on( 'error', function() {
                    errorEvent = true;
                });

                // Trigger the file input change
                // It's impossible to trigger this directly due
                // to browser security restrictions, so we call
                // the handler instead.
                view.handleInputChange( fakeEvent );
            });

            // Check that the image upload has completed,
            // either successfully or with an error.
            waitsFor(function() {
                return ( imageCapturedEvent || errorEvent );
            });

            // Execute the callback to check expectations.
            runs( callback );
        };

        var expectPreview = function( view, fileType ) {
            var previewImage = view.$preview.attr('src');
            if ( fileType ) {
                expect( previewImage ).toContain( 'data:image/' + fileType );
            } else {
                expect( previewImage ).toEqual( '' );
            }
        };

        var expectSubmitEnabled = function( isEnabled ) {
            var appearsDisabled = $( '#submit_button' ).hasClass( 'is-disabled' ),
                isDisabled = $( '#submit_button' ).prop( 'disabled' );

            expect( !appearsDisabled ).toEqual( isEnabled );
            expect( !isDisabled ).toEqual( isEnabled );
        };

        var expectImageData = function( view, fileType ) {
            var imageData = view.model.get( view.modelAttribute );
            if ( fileType ) {
                expect( imageData ).toContain( 'data:image/' + fileType );
            } else {
                expect( imageData ).toEqual( '' );
            }
        };

        var expectError = function( view ) {
            expect( view.errorModel.get('shown') ).toBe(true);
        };

        beforeEach(function() {
            setFixtures(
                '<div id="current-step-container"></div>' +
                '<input type="button" id="submit_button"></input>'
            );
            TemplateHelpers.installTemplate( 'templates/verify_student/image_input' );
        });

        it( 'initially disables the submit button', function() {
            createView();
            expectSubmitEnabled( false );
        });

        it( 'uploads a png image', function() {
            var view = createView();

            uploadImage( view, 'png', function() {
                expectPreview( view, 'png' );
                expectSubmitEnabled( true );
                expectImageData( view, 'png' );
            });
        });

        it( 'uploads a jpeg image', function() {
            var view = createView();

            uploadImage( view, 'jpeg', function() {
                expectPreview( view, 'jpeg' );
                expectSubmitEnabled( true );
                expectImageData( view, 'jpeg' );
            } );
        });

        it( 'hides the preview when the user cancels the upload', function() {
            var view = createView();

            uploadImage( view, null, function() {
                expectPreview( view, null );
                expectSubmitEnabled( false );
                expectImageData( view, null );
            } );
        });

        it( 'shows an error if the file type is not supported', function() {
            var view = createView();

            uploadImage( view, 'txt', function() {
                expectPreview( view, null );
                expectError( view );
                expectSubmitEnabled( false );
                expectImageData( view, null );
            } );
        });
    });
});
