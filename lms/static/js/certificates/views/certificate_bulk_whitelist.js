// Backbone Application View: CertificateBulkWhitelist View
/*global define, RequireJS */

;(function(define){
    'use strict';

    define([
            'jquery',
            'underscore',
            'gettext',
            'backbone'
        ],

        function($, _, gettext, Backbone){
            var DOM_SELECTORS = {
                bulk_exception: ".bulk-white-list-exception",
                upload_csv_button: ".upload-csv-button",
                browse_file: ".browse-file",
                bulk_white_list_exception_form: "form#bulk-white-list-exception-form"
            };

            var MESSAGE_GROUP = {
                successfully_added: 'successfully-added',
                general_errors: 'general-errors',
                data_format_error: 'data-format-error',
                user_not_exist: 'user-not-exist',
                user_already_white_listed: 'user-already-white-listed',
                user_not_enrolled: 'user-not-enrolled'
            };

            return Backbone.View.extend({
                el: DOM_SELECTORS.bulk_exception,
                events: {
                    'change #browseBtn': 'chooseFile',
                    'click .upload-csv-button': 'uploadCSV'
                },

                initialize: function(options){
                    // Re-render the view when an item is added to the collection
                    this.bulk_exception_url = options.bulk_exception_url;
                },

                render: function(){
                    var template = this.loadTemplate('certificate-bulk-white-list');
                    this.$el.html(template());
                },

                loadTemplate: function(name) {
                    var templateSelector = "#" + name + "-tpl",
                    templateText = $(templateSelector).text();
                    return _.template(templateText);
                },

                uploadCSV: function() {
                    var form = this.$el.find(DOM_SELECTORS.bulk_white_list_exception_form);
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
                    $(".results").empty();

                    // Display general error messages
                    if (data_from_server.general_errors.length) {
                        var errors = data_from_server.general_errors;
                        generate_div('msg-error', MESSAGE_GROUP.general_errors, gettext('Errors!'), errors);
                    }

                    // Display success message
                    if (data_from_server.success.length) {
                        var success_data = data_from_server.success;
                        generate_div(
                            'msg-success',
                            MESSAGE_GROUP.successfully_added,
                            get_text(success_data.length, MESSAGE_GROUP.successfully_added),
                            success_data
                        );
                    }

                    // Display data row error messages
                    if (Object.keys(data_from_server.row_errors).length) {
                        var row_errors = data_from_server.row_errors;

                        if (row_errors.data_format_error.length) {
                            var format_errors = row_errors.data_format_error;
                            generate_div(
                                'msg-error',
                                MESSAGE_GROUP.data_format_error,
                                get_text(format_errors.length, MESSAGE_GROUP.data_format_error),
                                format_errors
                            );
                        }
                        if (row_errors.user_not_exist.length) {
                            var user_not_exist = row_errors.user_not_exist;
                            generate_div(
                                'msg-error',
                                MESSAGE_GROUP.user_not_exist,
                                get_text(user_not_exist.length, MESSAGE_GROUP.user_not_exist),
                                user_not_exist
                            );
                        }
                        if (row_errors.user_already_white_listed.length) {
                            var user_already_white_listed = row_errors.user_already_white_listed;
                            generate_div(
                                'msg-error',
                                MESSAGE_GROUP.user_already_white_listed,
                                get_text(user_already_white_listed.length, MESSAGE_GROUP.user_already_white_listed),
                                user_already_white_listed
                            );
                        }
                        if (row_errors.user_not_enrolled.length) {
                            var user_not_enrolled = row_errors.user_not_enrolled;
                            generate_div(
                                'msg-error',
                                MESSAGE_GROUP.user_not_enrolled,
                                get_text(user_not_enrolled.length, MESSAGE_GROUP.user_not_enrolled),
                                user_not_enrolled
                            );
                        }
                    }

                    function generate_div(div_class, group, heading, display_data) {
                        // inner function generate div and display response messages.
                        $('<div/>', {
                            class: 'message ' + div_class + ' ' + group
                        }).appendTo('.results').prepend( "<b>" + heading + "</b>" );

                        for(var i = 0; i < display_data.length; i++){
                            $('<div/>', {
                                text: display_data[i]
                            }).appendTo('.results > .' + div_class + '.' + group);
                        }
                    }

                    function get_text(qty, group) {
                        // inner function to display appropriate heading text
                        var text;
                        switch(group) {
                            case MESSAGE_GROUP.successfully_added:
                                text = qty > 1 ? gettext(qty + ' learners are successfully added to exception list'):
                                    gettext(qty + ' learner is successfully added to the exception list');
                                break;

                            case MESSAGE_GROUP.data_format_error:
                                text = qty > 1 ? gettext(qty + ' records are not in correct format'):
                                    gettext(qty + ' record is not in correct format');
                                break;

                            case MESSAGE_GROUP.user_not_exist:
                                text = qty > 1 ? gettext(qty + ' learners do not exist in LMS'):
                                    gettext(qty + ' learner does not exist in LMS');
                                break;

                            case MESSAGE_GROUP.user_already_white_listed:
                                text = qty > 1 ? gettext(qty + ' learners are already white listed'):
                                    gettext(qty + ' learner is already white listed');
                                break;

                            case MESSAGE_GROUP.user_not_enrolled:
                                text = qty > 1 ? gettext(qty + ' learners are not enrolled in course'):
                                    gettext(qty + ' learner is not enrolled in course');
                                break;
                        }
                        return text;
                    }
                },

                chooseFile: function(event) {
                    if (event && event.preventDefault) { event.preventDefault(); }
                    if (event.currentTarget.files.length === 1) {
                        this.$el.find(DOM_SELECTORS.upload_csv_button).removeClass('is-disabled');
                        this.$el.find(DOM_SELECTORS.browse_file).val(
                            event.currentTarget.value.substring(event.currentTarget.value.lastIndexOf("\\") + 1));
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
