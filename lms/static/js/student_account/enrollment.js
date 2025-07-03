(function(define) {
    'use strict';

    define(['jquery', 'jquery.cookie'], function($) {
        const ErrorStatuses = {
            forbidden: 403,
            badRequest: 400
        };

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
                    if (jqXHR.status === ErrorStatuses.forbidden) {
                        if (responseData.user_message_url) {
                            this.redirect(responseData.user_message_url);
                        } else {
                            this.showMessage(responseData);
                        }
                    } else if (jqXHR.status === ErrorStatuses.badRequest) {
                        this.showMessage(responseData);
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
                const componentId = 'student-enrollment-feedback-error';
                const existing = document.getElementById(componentId);
                if (existing) {
                    existing.remove();
                }
                // Using a fixed dashboard URL as the redirect destination since this is the most logical
                // place for users to go after encountering an enrollment error. The URL is hardcoded
                // because environment variables are not injected into the HTML/JavaScript context.
                const DASHBOARD_URL = '/dashboard';
                const textContent = (message && message.detail) ? message.detail : String(message);
                const messageDiv = document.createElement('div');
                messageDiv.setAttribute('id', componentId);
                messageDiv.setAttribute('class', 'fixed-top d-flex justify-content-center align-items-center');
                messageDiv.style.cssText = [
                    'width:100vw',
                    'height:100vh',
                    'background:rgba(0,0,0,0.5)',
                    'z-index:9999'
                ].join(';');

                const buttonText = typeof gettext === 'function' ? gettext('Close') : 'Close';

                messageDiv.innerHTML = `
                  <div class="page-banner w-75 has-actions">
                    <div class="alert alert-warning" role="alert">
                      <div class="row w-100">
                        <div class="col d-flex align-items-center">
                          <span class="icon icon-alert fa fa-warning me-2" aria-hidden="true"></span>
                          <span class="message-content" style="min-width: 0; overflow-wrap: anywhere;">${textContent}</span>
                        </div>
                         <div class="nav-actions mt-3 flex-row-reverse d-none">
                          <button type="button" class="action-primary" id="enrollment-redirect-btn">${buttonText}</button>
                        </div>
                      </div>
                    </div>
                  </div>
                `;
                const actionContainer = messageDiv.querySelector('.nav-actions');
                actionContainer.classList.replace('d-none', 'd-flex');
                actionContainer.querySelector('button').addEventListener('click', () => this.redirect(DASHBOARD_URL) )
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

