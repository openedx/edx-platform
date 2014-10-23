var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.EnrollmentInterface = {
        courseUrl: '/enrollment/v0/course/',

        studentUrl: '/enrollment/v0/student',

        trackSelectionUrl: '/course_modes/choose/',

        headers: {
            'X-CSRFToken': $.cookie('csrftoken')
        },
        
        studentInformation: function(courseKey) {
            // retrieve student enrollment information
        },

        courseInformation: function(courseKey) {
            // retrieve course information from the enrollment API
        },

        modeInArray: function(modeObjects, targetMode) {
            // Check if a given course mode slug exists in an array of mode objects
            var result = _.find(modeObjects, function(mode) {
                return mode.slug === targetMode; 
            });

            /* _.find returns the first value which passes the provided truth test,
            /* or undefined if no values pass the test
             */
            return !_.isUndefined(result);
        },

        enroll: function(courseKey, forwardUrl){
            var me = this;
            // attempt to enroll a student in a course
            $.ajax({
                url: this.courseUrl + courseKey,
                type: 'POST',
                data: {},
                headers: this.headers
            }).done(function(data){
                me.postEnrollmentHandler(courseKey, data, forwardUrl);
            }
            ).fail(function(data, textStatus) {
                me.enrollmentFailureHandler(courseKey, data, forwardUrl);
            });
        },

        enrollmentFailureHandler: function(courseKey, data, forwardUrl) {
            // handle failures to enroll via the API
            if(data.status == 400) {
                /* This status code probably means we don't have permissions to register
                /* for this course; look at the contents of the response
                 */
                var course = $.parseJSON(data.responseText);
                // see if it's a professional ed course
                if( 'course_modes' in course && this.modeInArray(course.course_modes, 'professional') ) {
                    // forward appropriately
                    forwardUrl = this.trackSelectionUrl + courseKey;
                }
            }
            // TODO: if we have a paid registration mode, add item to the cart and send them along

            // TODO: we should figure out how to handle errors here
            window.location.href = forwardUrl;
        },

        postEnrollmentHandler: function(courseKey, data, forwardUrl) {
            // Determine whether or not the course needs to be redirected to
            // a particular page.
            var course = data.course,
                course_modes = course.course_modes;
            
            // send the user to the track selection page, because it will do the right thing
            forwardUrl = this.trackSelectionUrl + courseKey;

            window.location.href = forwardUrl;
        }
    };
})(jQuery, _, gettext);
