/**
 * Interface for retrieving webcam photos.
 * Supports both HTML5 and Flash.
 */
 var edx = edx || {};

 (function( $, _, Backbone, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.WebcamPhotoView = Backbone.View.extend({

        template: "#webcam_photo-tpl",

        backends: [
            {
                name: "html5",

                initialize: function( obj ) {
                    this.URL = (window.URL || window.webkitURL);
                    this.video = obj.video || "";
                    this.canvas = obj.canvas || "";
                    this.stream = null;

                    // Start the capture
                    this.getUserMediaFunc()(
                        {
                            video: true,

                            // Specify the `fake` constraint if we detect we are running in a test
                            // environment. In Chrome, this will do nothing, but in Firefox, it will
                            // instruct the browser to use a fake video device.
                            fake: window.location.hostname === 'localhost'
                        },
                        _.bind( this.getUserMediaCallback, this ),
                        _.bind( this.handleVideoFailure, this )
                    );
                },

                isSupported: function() {
                    return this.getUserMediaFunc() !== undefined;
                },

                snapshot: function() {
                    var video;

                    if ( this.stream ) {
                        video = this.getVideo();
                        this.getCanvas().getContext('2d').drawImage( video, 0, 0 );
                        video.pause();
                        return true;
                    }

                    return false;
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
                    var video = this.getVideo();
                    this.stream = stream;
                    video.src = this.URL.createObjectURL( stream );
                    video.play();
                },

                getVideo: function() {
                    return $( this.video ).first()[0];
                },

                getCanvas: function() {
                    return $( this.canvas ).first()[0];
                },

                handleVideoFailure: function() {
                    this.trigger(
                        'error',
                        gettext( 'Video Capture Error' ),
                        gettext( 'Please verify that your webcam is connected and that you have allowed your browser to access it.' )
                    );
                }
            },

            {
                name: "flash",

                initialize: function( obj ) {
                    this.wrapper = obj.wrapper || "";
                    this.imageData = "";

                    // Replace the camera section with the flash object
                    $( this.wrapper ).html( this.flashObjectTag() );

                    // Wait for the player to load, then verify camera support
                    // Trigger an error if no camera is available.
                    this.checkCameraSupported();
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
                        return true;
                    }
                    return false;
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
                            'data="/static/js/verify_student/CameraCapture.swf" ' +
                            'width="500" ' +
                            'height="375">' +
                         '<param name="quality" value="high">' +
                         '<param name="allowscriptaccess" value="sameDomain">' +
                         '</object>'
                    );
                },

                getFlashObject: function() {
                    return $( "#flash_video" )[0];
                },

                checkCameraSupported: function() {
                    var flashObj = this.getFlashObject(),
                        isLoaded = false,
                        hasCamera = false;

                    isLoaded = (
                        flashObj &&
                        flashObj.hasOwnProperty( 'percentLoaded' ) &&
                        flashObj.percentLoaded() === 100
                    );

                    // On some browsers, the flash object will say it has a camera
                    // even "percentLoaded" isn't defined.
                    hasCamera = (
                        flashObj &&
                        flashObj.hasOwnProperty( 'hasCamera' ) &&
                        flashObj.hasCamera()
                    );

                    // If we've fully loaded, and no camera is available,
                    // then show an error.
                    if ( isLoaded && !hasCamera ) {
                        this.trigger(
                            'error',
                            gettext( "No Webcam Detected" ),
                            gettext( "You don't seem to have a webcam connected." ) + "  " +
                            gettext( "Double-check that your webcam is connected and working to continue.")
                        );
                    }

                    // If we're still waiting for the player to load, check
                    // back later.
                    else if ( !isLoaded && !hasCamera ) {
                        setTimeout( _.bind( this.checkCameraSupported, this ), 50 );
                    }

                    // Otherwise, the flash player says it has a camera,
                    // so we don't need to keep checking.
                }
            }
        ],

        initialize: function( obj ) {
            this.submitButton = obj.submitButton || "";
            this.modelAttribute = obj.modelAttribute || "";
            this.errorModel = obj.errorModel || null;
            this.backend = _.find(
                obj.backends || this.backends,
                function( backend ) {
                    return backend.isSupported();
                }
            );

            if ( !this.backend ) {
                this.handleError(
                    gettext( "Flash Not Detected" ),
                    gettext( "You don't seem to have Flash installed." ) + "  " +
                    _.sprintf(
                        gettext( "%(a_start)s Get Flash %(a_end)s to continue your enrollment." ),
                        {
                            a_start: '<a rel="external" href="http://get.adobe.com/flashplayer/">',
                            a_end: '</a>'
                        }
                    )
                );
            }
            else {
                _.extend( this.backend, Backbone.Events );
                this.listenTo( this.backend, 'error', this.handleError );
            }
        },

        render: function() {
            var renderedHtml;

            // Set the submit button to disabled by default
            this.setSubmitButtonEnabled( false );

            // Load the template for the webcam into the DOM
            renderedHtml = _.template( $( this.template ).html(), {} );
            $( this.el ).html( renderedHtml );

            // Initialize the video capture backend
            // We need to do this after rendering the template
            // so that the backend has the opportunity to modify the DOM.
            if ( this.backend ) {
                this.backend.initialize({
                    wrapper: "#camera",
                    video: '#photo_id_video',
                    canvas: '#photo_id_canvas'
                });

                // Install event handlers
                $( "#webcam_reset_button", this.el ).on( 'click', _.bind( this.reset, this ) );
                $( "#webcam_capture_button", this.el ).on( 'click', _.bind( this.capture, this ) );

                // Show the capture button
                $( "#webcam_capture_button", this.el ).removeClass('is-hidden');
            }

            return this;
        },

        reset: function() {
            // Disable the submit button
            this.setSubmitButtonEnabled( false );

            // Reset the video capture
            this.backend.reset();

            // Reset data on the model
            this.model.set( this.modelAttribute, "" );

            // Go back to the initial button state
            $( "#webcam_reset_button", this.el ).addClass('is-hidden');
            $( "#webcam_capture_button", this.el ).removeClass('is-hidden');
        },

        capture: function() {
            // Take a snapshot of the video
            var success = this.backend.snapshot();

            if ( success ) {
                // Trigger an event which parent views can use to fire a
                // business intelligence event
                this.trigger( 'imageCaptured' );

                // Hide the capture button, and show the reset button
                $( "#webcam_capture_button", this.el ).addClass('is-hidden');
                $( "#webcam_reset_button", this.el ).removeClass('is-hidden');

                // Save the data to the model
                this.model.set( this.modelAttribute, this.backend.getImageData() );

                // Enable the submit button
                this.setSubmitButtonEnabled( true );
            }
        },

        handleError: function( errorTitle, errorMsg ) {
            // Hide the buttons
            $( "#webcam_capture_button", this.el ).addClass('is-hidden');
            $( "#webcam_reset_button", this.el ).addClass('is-hidden');

            // Show the error message
            if ( this.errorModel ) {
                this.errorModel.set({
                    errorTitle: errorTitle,
                    errorMsg: errorMsg,
                    shown: true
                });
            }
        },

        setSubmitButtonEnabled: function( isEnabled ) {
            $( this.submitButton )
                .toggleClass( 'is-disabled', !isEnabled )
                .prop( 'disabled', !isEnabled )
                .attr('aria-disabled', !isEnabled);
        }
    });

 })( jQuery, _, Backbone, gettext );
