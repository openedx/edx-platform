;(function (define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'gettext',
        'support/js/collections/certificate',
        'text!support/templates/certificates.underscore',
        'text!support/templates/certificates_results.underscore'
    ], function (Backbone, _, gettext, CertCollection, certificatesTpl, resultsTpl) {
        return Backbone.View.extend({
            events: {
                'submit .certificates-form': 'search',
                'click .btn-cert-regenerate': 'regenerateCertificate'
            },

            initialize: function(options) {
                _.bindAll(this, 'search', 'updateCertificates', 'regenerateCertificate', 'handleSearchError');
                this.certificates = new CertCollection({});
                this.initialQuery = options.userQuery || null;
            },

            render: function() {
                this.$el.html(_.template(certificatesTpl));

                // If there is an initial query, then immediately trigger a search.
                // This is useful because it allows users to share search results:
                // if the URL contains ?query="foo" then anyone who loads that URL
                // will automatically search for "foo".
                if (this.initialQuery) {
                    this.setUserQuery(this.initialQuery);
                    this.triggerSearch();
                }

                return this;
            },

            renderResults: function() {
                var context = {
                    certificates: this.certificates,
                };

                this.setResults(_.template(resultsTpl, context));
            },

            renderError: function(error) {
                var errorMsg = error || gettext('An unexpected error occurred.  Please try again.');
                this.setResults(errorMsg);
            },

            search: function(event) {

                // Fetch the certificate collection for the given user
                var query = this.getUserQuery(),
                    url = '/support/certificates?query=' + query;

                // Prevent form submission, since we're handling it ourselves.
                event.preventDefault();

                // Push a URL into history with the search query as a GET parameter.
                // That way, if the user reloads the page or sends someone the link
                // then the same search will be performed on page load.
                window.history.pushState({}, window.document.title, url);

                // Perform a search for the user's certificates.
                this.disableButtons();
                this.certificates.setUserQuery(query);
                this.certificates.fetch({
                    success: this.updateCertificates,
                    error: this.handleSearchError
                });
            },

            regenerateCertificate: function(event) {
                var $button = $(event.target);

                // Regenerate certificates for a particular user and course.
                // If this is successful, reload the certificate results so they show
                // the updated status.
                this.disableButtons();
                $.ajax({
                    url: '/certificates/regenerate',
                    type: 'POST',
                    data: {
                        username: $button.data('username'),
                        course_key: $button.data('course-key'),
                    },
                    context: this,
                    success: function() {
                        this.certificates.fetch({
                            success: this.updateCertificates,
                            error: this.handleSearchError,
                        });
                    },
                    error: this.handleRegenerateError
                });
            },

            updateCertificates: function() {
                this.renderResults();
                this.enableButtons();
            },

            handleSearchError: function(jqxhr) {
                this.renderError(jqxhr.responseText);
                this.enableButtons();
            },

            handleRegenerateError: function(jqxhr) {
                // Since there are multiple "regenerate" buttons on the page,
                // it's difficult to show the error message in the UI.
                // Since this page is used only by internal staff, I think the
                // quick-and-easy way is reasonable.
                alert(jqxhr.responseText);
                this.enableButtons();
            },

            triggerSearch: function() {
                $('.certificates-form').submit();
            },

            getUserQuery: function() {
                return $('.certificates-form input[name="query"]').val();
            },

            setUserQuery: function(query) {
                $('.certificates-form input[name="query"]').val(query);
            },

            setResults: function(html) {
                $(".certificates-results", this.$el).html(html);
            },

            disableButtons: function() {
                $('.btn-disable-on-submit')
                    .addClass("is-disabled")
                    .attr("disabled", true);
            },

            enableButtons: function() {
                $('.btn-disable-on-submit')
                    .removeClass('is-disabled')
                    .attr('disabled', false);
            }
        });
    });
}).call(this, define || RequireJS.define);
