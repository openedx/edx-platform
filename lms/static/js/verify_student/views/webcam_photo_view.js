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

                    // Start the capture
                    this.getUserMediaFunc()(
                        { video: true },
                        _.bind( this.getUserMediaCallback, this ),
                        _.bind( this.handleVideoFailure, this )
                    );
                },

                isSupported: function() {
                    return (this.getUserMediaFunc() !== undefined);
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

                getUserMediaFunc: function() {
                    var userMedia = (
                        navigator.getUserMedia || navigator.webkitGetUserMedia ||
                        navigator.mozGetUserMedia || navigator.msGetUserMedia
                    );

                    if ( userMedia ) {
                        return _.bind( userMedia, navigator );
                    }
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
                initialize: function( obj ) {
                    this.wrapper = obj.wrapper || "";
                    this.imageData = "";

                    // Replace the camera section with the flash object
                    $( this.wrapper ).html( this.flashObjectTag() );
                },

                isSupported: function() {
                    try {
                        var flashObj = new ActiveXObject('ShockwaveFlash.ShockwaveFlash');
                        if ( flashObj ) {
                            return true;
                        }
                    } catch(ex) {
                        if ( navigator.mimeTypes["application/x-shockwave-flash"] !== undefined ) {
                            return true;
                        }
                    }

                    return false;
                },

                snapshot: function() {
                    var flashObj = this.getFlashObject();
                    if ( flashObj.cameraAuthorized() ) {
                        this.imageData = flashObj.snap();
                    }
                },

                reset: function() {
                    this.getFlashObject().reset();
                },

                getImageData: function() {
                    return this.imageData;
                },

                flashObjectTag: function() {
                    return (
                        '<object type="application/x-shockwave-flash" ' +
                            'id="flash_video" ' +
                            'name="flash_video" ' +
                            'data="/static/js/verify_student/CameraCapture.swf?v=3" ' +
                            'width="500" ' +
                            'height="375">' +
                         '<param name="quality" value="high">' +
                         '<param name="allowscriptaccess" value="sameDomain">' +
                         '</object>'
                    );
                },

                getFlashObject: function() {
                    return $( "#flash_video" )[0];
                }
            }
        },

        videoBackendPriority: ['html5', 'flash'],

        initialize: function( obj ) {
            this.submitButton = obj.submitButton || "";
            this.modelAttribute = obj.modelAttribute || "";
            //this.backend = this.chooseVideoCaptureBackend();
            this.backend = this.videoCaptureBackend.flash;

            if ( !this.backend ) {
                // TODO -- actual error
                console.log("No video backend available");
            }

        },

        render: function() {
            var renderedHtml;

            // Load the template for the webcam into the DOM
            renderedHtml = _.template( $( this.template ).html(), {} );
            $( this.el ).html( renderedHtml );

            // Initialize the video capture backend
            // We need to do this after rendering the template
            // so that the backend has the opportunity to modify the DOM.
            this.backend.initialize({
                wrapper: "#camera",
                video: '#photo_id_video',
                canvas: '#photo_id_canvas'
            });

            // Install event handlers
            $( "#webcam_reset_button", this.el ).click( _.bind( this.reset, this ) );
            $( "#webcam_capture_button", this.el ).click( _.bind( this.capture, this ) );
            $( "#webcam_approve_button", this.el ).click( _.bind( this.approve, this ) );

            return this;
        },

        reset: function() {
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
            // Take a snapshot of the video
            this.backend.snapshot();

            // Show the reset and approve buttons
            $( "#webcam_capture_button" ).hide();
            $( "#webcam_reset_button", this.el ).show();
            $( "#webcam_approve_button", this.el ).show();
        },

        approve: function() {
            // Save the data to the model
            this.model.set( this.modelAttribute, this.backend.getImageData() );

            // Make the "approve" button green
            $( "#webcam_approve_button" ).addClass( "approved" );

            // Enable the submit button
            $( this.submitButton ).removeClass( "is-disabled" );
        },

        chooseVideoCaptureBackend: function() {
            var i, backendName, backend;

            for ( i = 0; i < this.videoBackendPriority.length; i++ ) {
                backendName = this.videoBackendPriority[i];
                backend = this.videoCaptureBackend[backendName];
                if ( backend.isSupported() ) {
                    return backend;
                }
            }
        }

    });

 })( jQuery, _, Backbone );
