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
                    } else if (jqXHR.status === 400) {
                        // Show the error message for bad requests (invalid enrollment data)
                        this.showMessage(responseData);
                        // Add timeout before redirecting to allow user to see the message
                        var self = this;
                        setTimeout(function() {
                            // Redirect to the provided redirectUrl after 5 seconds
                            if (redirectUrl) {
                                self.redirect(redirectUrl);
                            }
                        }, 6000); // 6000 milliseconds = 6 seconds
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
                console.log('showMessage called', message);
                var existing = document.getElementById('messageDiv');
                if (existing) {
                    existing.remove();
                }
                var messageDiv = document.createElement('div');
                messageDiv.setAttribute('id', 'messageDiv');

                // Style for popup
                messageDiv.style.cssText = [
                    'position:fixed',
                    'top:0',
                    'left:0',
                    'width:100vw',
                    'height:100vh',
                    'display:flex',
                    'align-items:center',
                    'justify-content:center',
                    'background:rgba(0,0,0,0.3)',
                    'z-index:9999'
                ].join(';');

                // Internal div inside the popup
                var innerDiv = document.createElement('div');
                innerDiv.style.cssText = [
                    'background:#fff3cd',
                    'color:#856404',
                    'border:1px solid #ffeeba',
                    'padding:24px 32px',
                    'border-radius:8px',
                    'max-width:600px',
                    'font-weight:bold',
                    'text-align:center',
                    'font-size:1.1em',
                    'box-shadow:0 4px 24px rgba(0,0,0,0.15)'
                ].join(';');
                innerDiv.textContent = message && message.detail ? message.detail : String(message);

                messageDiv.appendChild(innerDiv);
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
