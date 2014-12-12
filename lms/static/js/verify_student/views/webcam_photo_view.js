/**
 * Interface for retrieving webcam photos.
 * Supports both HTML5 and Flash.
 */
 var edx = edx || {};

 (function( $, _, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.WebcamPhotoView = Backbone.View.extend({

        template: "#webcam_photo-tpl",

        videoCaptureBackend: {
            html5: {
                initialize: function( obj ) {
                    this.URL = (window.URL || window.webkitURL);
                    this.video = obj.video || "";
                    this.canvas = obj.canvas || "";
                    this.stream = null;
                },

                isSupported: function() {
                    return (this.getUserMediaFunc() !== undefined);
                },

                getUserMediaFunc: function() {
                    var userMedia = (
                        navigator.getUserMedia || navigator.webkitGetUserMedia ||
                        navigator.mozGetUserMedia || navigator.msGetUserMedia
                    );

                    if ( userMedia ) {
                        return _.bind( userMedia, navigator );
                    }
                },

                startCapture: function() {
                    this.getUserMediaFunc()(
                        { video: true },
                        _.bind( this.getUserMediaCallback, this ),
                        _.bind( this.handleVideoFailure, this )
                    );
                },

                snapshot: function() {
                    var video;

                    if ( this.stream ) {
                        video = this.getVideo();
                        this.getCanvas().getContext('2d').drawImage( video, 0, 0 );
                        video.pause();
                    }
                },

                getImageData: function() {
                    return this.getCanvas().toDataURL( 'image/png' );
                },

                reset: function() {
                    this.getVideo().play();
                },

                getUserMediaCallback: function( stream ) {
                    this.stream = stream;
                    this.getVideo().src = this.URL.createObjectURL( stream );
                    this.getVideo().play();
                },

                getVideo: function() {
                    return $( this.video ).first()[0];
                },

                getCanvas: function() {
                    return $( this.canvas ).first()[0];
                },

                handleVideoFailure: function( error ) {
                    // TODO
                    console.log("Video failure", error);
                }
            },

            flash: {
                initialize: function() {

                },

                isSupported: function() {
                    var hasFlash = false;
                    try {
                        var flashObject = new ActiveXObject( 'ShockwaveFlash.ShockwaveFlash' );
                        if ( flashObject ) {
                            hasFlash = true;
                        }
                    }
                    catch (ex) {
                        if ( navigator.mimeTypes[ 'application/x-shockwave-flash' ] !== undefined ) {
                            hasFlash = true;
                        }
                    }

                    if ( hasFlash ) {
                        return this.flashObject.hasOwnProperty( 'hasCamera' );
                    }
                    else {
                        return false;
                    }
                },

                startCapture: function() {

                }
            }
        },

        videoBackendPriority: ['html5', 'flash'],

        initialize: function( obj ) {
            this.submitButton = obj.submitButton || "";
            this.modelAttribute = obj.modelAttribute || "";

            // TODO: make this decision based on priorities
            this.backend = this.videoCaptureBackend.html5;
            this.backend.initialize({
                video: '#photo_id_video',
                canvas: '#photo_id_canvas'
            });
        },

        render: function() {
            var renderedHtml;

            // Load the template for the webcam into the DOM
            renderedHtml = _.template( $( this.template ).html(), {} );
            $( this.el ).html( renderedHtml );

            // Install event handlers
            $( "#webcam_reset_button", this.el ).click( _.bind( this.reset, this ) );
            $( "#webcam_capture_button", this.el ).click( _.bind( this.capture, this ) );
            $( "#webcam_approve_button", this.el ).click( _.bind( this.approve, this ) );

            // Start the video capture
            this.backend.startCapture();

            return this;
        },

        reset: function() {
            // DEBUG
            console.log("Reset");

            // Disable the submit button
            $( this.submitButton ).addClass( "is-disabled" );

            // Reset the video capture
            this.backend.reset();

            // Go back to the initial button state
            $( "#webcam_reset_button", this.el ).hide();
            $( "#webcam_approve_button", this.el ).removeClass( "approved" ).hide();
            $( "#webcam_capture_button" ).show();
        },

        capture: function() {
            // DEBUG
            console.log("Capture");

            // Take a snapshot of the video
            this.backend.snapshot();

            // Show the reset and approve buttons
            $( "#webcam_capture_button" ).hide();
            $( "#webcam_reset_button", this.el ).show();
            $( "#webcam_approve_button", this.el ).show();
        },

        approve: function() {
            // DEBUG
            console.log("Approve");

            // Save the data to the model
            this.model.set( this.modelAttribute, this.backend.getImageData() );

            // Make the "approve" button green
            $( "#webcam_approve_button" ).addClass( "approved" );

            // Enable the submit button
            $( this.submitButton ).removeClass( "is-disabled" );
        }

    });

 })( jQuery, _, Backbone );
