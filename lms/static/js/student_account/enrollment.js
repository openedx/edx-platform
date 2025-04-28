(function(define) {
    'use strict';

    define(['jquery', 'jquery.cookie'], function($) {
        var EnrollmentInterface = {

            urls: {
                baskets: '/api/commerce/v0/baskets/'
            },

            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },

            /**
             * Enroll a user in a course, then redirect the user.
             * @param  {string} courseKey  Slash-separated course key.
             * @param  {string} redirectUrl The URL to redirect to once enrollment completes.
             */
            enroll: function(courseKey, redirectUrl) {
                var data_obj = {course_id: courseKey},
                    data = JSON.stringify(data_obj);

                $.ajax({
                    url: this.urls.baskets,
                    type: 'POST',
                    contentType: 'application/json; charset=utf-8',
                    data: data,
                    headers: this.headers,
                    context: this
                }).fail(function(jqXHR) {
                    var responseData = JSON.parse(jqXHR.responseText);
                    if (jqXHR.status === 403 && responseData.user_message_url) {
                        // Check if we've been blocked from the course
                        // because of country access rules.
                        // If so, redirect to a page explaining to the user
                        // why they were blocked.
                        this.redirect(responseData.user_message_url);
                    } else if (jqXHR.status === 403 && !responseData.user_message_url) {
                        // If we are blocked but no user_message_url is provided,
                        // show the JSON response in the frontend.
                        this.showMessage(responseData);

                        // Add timeout before redirecting to allow user to see the message
                        var self = this;
                        setTimeout(function() {
                            // Redirect to the provided redirectUrl after 5 seconds
                            if (redirectUrl) {
                                self.redirect(redirectUrl);
                            }
                        }, 5000); // 5000 milliseconds = 5 seconds
                    } else {
                        // Otherwise, redirect the user to the next page.
                        if (redirectUrl) {
                            this.redirect(redirectUrl);
                        }
                    }
                }).done(function(response) {
                    // If we successfully enrolled, redirect the user
                    // to the next page (usually the student dashboard or payment flow)
                    if (response.redirect_destination) {
                        this.redirect(response.redirect_destination);
                    } else if (redirectUrl) {
                        this.redirect(redirectUrl);
                    }
                });
            },
            /**
             * Show a message in the frontend.
             * @param  {Object} message The message to display.
             */
            showMessage: function(message) {
                // Create a new div element
                var messageDiv = document.createElement('div');
                messageDiv.setAttribute('id', 'messageDiv');
                messageDiv.style.color = 'red'; // Example styling
                messageDiv.style.marginTop = '40px';

                // Set the message content
                messageDiv.textContent = JSON.stringify(message);

                // Append the messageDiv to the body or a specific container
                document.body.appendChild(messageDiv);
            },

            /**
             * Redirect to a URL.  Mainly useful for mocking out in tests.
             * @param  {string} url The URL to redirect to.
             */
            redirect: function(url) {
                window.location.href = url;
            }
        };

        return EnrollmentInterface;
    });
}).call(this, define || RequireJS.define);
