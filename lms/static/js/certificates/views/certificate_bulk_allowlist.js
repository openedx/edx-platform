// Backbone Application View: CertificateBulkAllowlist View
/* global define, RequireJS */

(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'gettext',
        'backbone'
    ],

    function($, _, gettext, Backbone) {
        var DOM_SELECTORS = {
            bulk_exception: '.bulk-allowlist-exception',
            upload_csv_button: '.upload-csv-button',
            browse_file: '.browse-file',
            bulk_allowlist_exception_form: 'form#bulk-allowlist-exception-form'
        };

        var MESSAGE_GROUP = {
            successfully_added: 'successfully-added',
            general_errors: 'general-errors',
            data_format_error: 'data-format-error',
            user_not_exist: 'user-not-exist',
            user_already_allowlisted: 'user-already-allowlisted',
            user_not_enrolled: 'user-not-enrolled',
            user_on_certificate_invalidation_list: 'user-on-certificate-invalidation-list'
        };

        return Backbone.View.extend({
            el: DOM_SELECTORS.bulk_exception,
            events: {
                'change #browseBtn-bulk-csv': 'chooseFile',
                'click .upload-csv-button': 'uploadCSV',
                'click .arrow': 'toggleMessageDetails'
            },

            initialize: function(options) {
                // Re-render the view when an item is added to the collection
                this.bulk_exception_url = options.bulk_exception_url;
            },

            render: function() {
                var template = this.loadTemplate('certificate-bulk-allowlist');
                this.$el.html(template()); // xss-lint: disable=javascript-jquery-html
            },

            loadTemplate: function(name) {
                var templateSelector = '#' + name + '-tpl',
                    templateText = $(templateSelector).text();
                return _.template(templateText);
            },

            uploadCSV: function() {
                var form = this.$el.find(DOM_SELECTORS.bulk_allowlist_exception_form);
                var self = this;
                form.unbind('submit').submit(function(e) {
                    var data = new FormData(e.currentTarget);
                    $.ajax({
                        dataType: 'json',
                        type: 'POST',
                        url: self.bulk_exception_url,
                        data: data,
                        processData: false,
                        contentType: false,
                        success: function(data_from_server) {
                            self.display_response(data_from_server);
                        }
                    });
                    e.preventDefault(); // avoid to execute the actual submit of the form.
                });
            },

            display_response: function(data_from_server) {
                var UserOnCertificateInvalidationList;

                $('.bulk-exception-results').removeClass('hidden').empty();

                function generateDiv(group, heading, displayData) {
                    // inner function generate div and display response messages.
                    $('<div/>', {
                        class: 'message ' + group
                    }).appendTo('.bulk-exception-results').prepend( // eslint-disable-line max-len, xss-lint: disable=javascript-jquery-insert-into-target,javascript-jquery-prepend
                        "<button type='button' id= '" + group + "' class='arrow'> + </button>" + heading) // eslint-disable-line max-len, xss-lint: disable=javascript-concat-html
                        .append($('<ul/>', {
                            class: group
                        }));

                    for (var i = 0; i < displayData.length; i++) { // eslint-disable-line vars-on-top
                        $('<li/>', {
                            text: displayData[i]
                        }).appendTo('div.message > .' + group); // eslint-disable-line max-len, xss-lint: disable=javascript-jquery-insert-into-target
                    }
                    $('div.message > .' + group).hide();
                }

                function getDisplayText(qty, group) {
                    // inner function to display appropriate heading text
                    var text;

                    switch (group) {
                    case MESSAGE_GROUP.successfully_added:
                        text = qty > 1 ?
                            gettext(qty + ' learners were successfully added to exception list') :
                            gettext(qty + ' learner was successfully added to the exception list');
                        break;

                    case MESSAGE_GROUP.data_format_error:
                        text = qty > 1 ?
                            gettext(qty + ' records are not in the correct format and have not been added to' +
                                    ' the exception list') :
                            gettext(qty + ' record is not in the correct format and has not been added to the' +
                                    ' exception list');
                        break;

                    case MESSAGE_GROUP.user_not_exist:
                        text = qty > 1 ?
                            gettext(qty + ' learner accounts cannot be found and have not been added to the ' +
                                    'exception list') :
                            gettext(qty + ' learner account cannot be found and has not been added to the' +
                                    ' exception list');
                        break;

                    case MESSAGE_GROUP.user_already_allowlisted:
                        text = qty > 1 ?
                            gettext(qty + ' learners already appear on the exception list in this course') :
                            gettext(qty + ' learner already appears on the exception list in this course');
                        break;

                    case MESSAGE_GROUP.user_not_enrolled:
                        text = qty > 1 ?
                            gettext(qty + ' learners are not enrolled in this course and have not added to the' +
                                    ' exception list') :
                            gettext(qty + ' learner is not enrolled in this course and has not been added to the' +
                                    ' exception list');
                        break;

                    case MESSAGE_GROUP.user_on_certificate_invalidation_list:
                        text = qty > 1 ?
                            gettext(qty + ' learners have an active certificate invalidation in this course and' +
                                    ' have not been added to the exception list') :
                            gettext(qty + ' learner has an active certificate invalidation in this course and has' +
                                    ' not been added to the exception list');
                        break;

                    default:
                        text = qty > 1 ?
                            gettext(qty + ' learners encountered unknown errors') :
                            gettext(qty + ' learner encountered an unknown error');
                        break;
                    }

                    return text;
                }

                // Display general error messages
                if (data_from_server.general_errors.length) {
                    var errors = data_from_server.general_errors;
                    generateDiv(
                        MESSAGE_GROUP.general_errors,
                        gettext('Uploaded file issues. Click on "+" to view.'),
                        errors
                    );
                }

                // Display success message
                if (data_from_server.success.length) {
                    var success_data = data_from_server.success;
                    generateDiv(
                        MESSAGE_GROUP.successfully_added,
                        getDisplayText(success_data.length, MESSAGE_GROUP.successfully_added),
                        success_data
                    );
                }

                // Display data row error messages
                if (Object.keys(data_from_server.row_errors).length) {
                    var row_errors = data_from_server.row_errors;

                    if (row_errors.data_format_error.length) {
                        var format_errors = row_errors.data_format_error;
                        generateDiv(
                            MESSAGE_GROUP.data_format_error,
                            getDisplayText(format_errors.length, MESSAGE_GROUP.data_format_error),
                            format_errors
                        );
                    }
                    if (row_errors.user_not_exist.length) {
                        var user_not_exist = row_errors.user_not_exist;
                        generateDiv(
                            MESSAGE_GROUP.user_not_exist,
                            getDisplayText(user_not_exist.length, MESSAGE_GROUP.user_not_exist),
                            user_not_exist
                        );
                    }
                    if (row_errors.user_already_allowlisted.length) {
                        var user_already_allowlisted = row_errors.user_already_allowlisted;
                        generateDiv(
                            MESSAGE_GROUP.user_already_allowlisted,
                            getDisplayText(
                                user_already_allowlisted.length,
                                MESSAGE_GROUP.user_already_allowlisted
                            ),
                            user_already_allowlisted
                        );
                    }
                    if (row_errors.user_not_enrolled.length) {
                        var user_not_enrolled = row_errors.user_not_enrolled;
                        generateDiv(
                            MESSAGE_GROUP.user_not_enrolled,
                            getDisplayText(user_not_enrolled.length, MESSAGE_GROUP.user_not_enrolled),
                            user_not_enrolled
                        );
                    }
                    if (row_errors.user_on_certificate_invalidation_list.length) {
                        UserOnCertificateInvalidationList =
                                row_errors.user_on_certificate_invalidation_list;
                        generateDiv(
                            MESSAGE_GROUP.user_on_certificate_invalidation_list,
                            getDisplayText(
                                UserOnCertificateInvalidationList.length,
                                MESSAGE_GROUP.user_on_certificate_invalidation_list
                            ),
                            UserOnCertificateInvalidationList
                        );
                    }
                }
            },

            toggleMessageDetails: function(event) {
                if (event && event.preventDefault) { event.preventDefault(); }
                var group = event.target.id;
                $('div.message > .' + group).slideToggle('fast', function() {
                    if ($(this).is(':visible')) {
                        event.target.text = ' -- ';
                    } else {
                        event.target.text = ' + ';
                    }
                });
            },

            chooseFile: function(event) {
                if (event && event.preventDefault) { event.preventDefault(); }
                if (event.currentTarget.files.length === 1) {
                    this.$el.find(DOM_SELECTORS.upload_csv_button).removeAttr('disabled');
                    this.$el.find(DOM_SELECTORS.browse_file).val(
                        event.currentTarget.value.substring(event.currentTarget.value.lastIndexOf('\\') + 1));
                }
            }
        });
    }
    );
}).call(this, define || RequireJS.define);
