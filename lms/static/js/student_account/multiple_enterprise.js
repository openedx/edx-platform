(function(define) {
    'use strict';
    define(['jquery', 'js/student_account/utils', 'jquery.cookie'], function($, Utils) {
        var MultipleEnterpriseInterface = {

            urls: {
                learners: '/enterprise/api/v1/enterprise-learner/',
                multipleEnterpriseUrl: '/enterprise/select/active/?success_url='
            },

            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },

            /**
             * Fetch the learner data, then redirect the user to a enterprise selection page if multiple
             * enterprises were found.
             * @param  {string} nextUrl The URL to redirect to after multiple enterprise selection.
             */
            check: function(nextUrl) {
                var redirectUrl = this.urls.multipleEnterpriseUrl + encodeURI(nextUrl);
                var username = Utils.userFromEdxUserCookie().username;
                var next = nextUrl || '/';
                $.ajax({
                    url: this.urls.learners + '?username=' + username,
                    type: 'GET',
                    contentType: 'application/json; charset=utf-8',
                    headers: this.headers,
                    context: this
                }).fail(function() {
                    this.redirect(next);
                }).done(function(response) {
                    if (response.count > 1 && redirectUrl) {
                        this.redirect(redirectUrl);
                    } else {
                        this.redirect(next);
                    }
                });
            },

            /**
             * Redirect to a URL.
             * @param  {string} url The URL to redirect to.
             */
            redirect: function(url) {
                window.location.href = url;
            }
        };

        return MultipleEnterpriseInterface;
    });
}).call(this, define || RequireJS.define);
