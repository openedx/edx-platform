/* eslint-disable-next-line no-use-before-define, no-var */
var edx = edx || {};

(function(Backbone, $, _, gettext) {
    'use strict';

    edx.instructor_dashboard = edx.instructor_dashboard || {};
    edx.instructor_dashboard.ecommerce = {};

    edx.instructor_dashboard.ecommerce.ExpiryCouponView = Backbone.View.extend({
        el: 'li#add-coupon-modal-field-expiry',
        events: {
            'click input[type="checkbox"]': 'clicked'
        },
        initialize: function() {
            $('li#add-coupon-modal-field-expiry input[name="expiration_date"]').hide();
            _.bindAll(this, 'clicked');
        },
        clicked: function(event) {
            if (event.currentTarget.checked) {
                this.show(this.$('#coupon_expiration_date'));
                this.$el.find('#coupon_expiration_date').focus();
            } else {
                this.hide(this.$('#coupon_expiration_date'));
            }
        },
        show: function($el) {
            $el.css('display', 'inline');
        },
        hide: function($el) {
            $el.css('display', 'none');
        }
    });

    $(function() {
        /* eslint-disable-next-line camelcase, no-var */
        var $registration_code_status_form = $('form#set_regcode_status_form'),
            // eslint-disable-next-line camelcase
            $lookup_button = $('#lookup_regcode', $registration_code_status_form),
            // eslint-disable-next-line camelcase
            $registration_code_status_form_error = $('#regcode_status_form_error', $registration_code_status_form),
            // eslint-disable-next-line camelcase
            $registration_code_status_form_success = $('#regcode_status_form_success', $registration_code_status_form);

        $('#coupon_expiration_date').datepicker({
            minDate: 0
        });
        /* eslint-disable-next-line no-unused-vars, no-var */
        var view = new edx.instructor_dashboard.ecommerce.ExpiryCouponView();
        $('input[name="user-enrollment-report"]').click(function() {
            // eslint-disable-next-line no-var
            var url = $(this).data('endpoint');
            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: url,
                success: function(data) {
                    $('#enrollment-report-request-response').text(data.status);
                    return $('#enrollment-report-request-response').css({
                        display: 'block'
                    });
                },
                /* eslint-disable-next-line camelcase, no-unused-vars */
                error: function(std_ajax_err) {
                    $('#enrollment-report-request-response-error').text(gettext('There was a problem creating the report. Select "Create Executive Summary" to try again.'));
                    return $('#enrollment-report-request-response-error').css({
                        display: 'block'
                    });
                }
            });
        });
        $('input[name="exec-summary-report"]').click(function() {
            // eslint-disable-next-line no-var
            var url = $(this).data('endpoint');
            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: url,
                success: function(data) {
                    $('#exec-summary-report-request-response').text(data.status);
                    return $('#exec-summary-report-request-response').css({
                        display: 'block'
                    });
                },
                /* eslint-disable-next-line camelcase, no-unused-vars */
                error: function(std_ajax_err) {
                    $('#exec-summary-report-request-response-error').text(gettext('There was a problem creating the report. Select "Create Executive Summary" to try again.'));
                    return $('#exec-summary-report-request-response-error').css({
                        display: 'block'
                    });
                }
            });
        });
        /* eslint-disable-next-line camelcase, consistent-return */
        $lookup_button.click(function() {
            // eslint-disable-next-line camelcase
            $registration_code_status_form_error.hide();
            // eslint-disable-next-line camelcase
            $lookup_button.attr('disabled', true);
            // eslint-disable-next-line no-var
            var url = $(this).data('endpoint');
            /* eslint-disable-next-line camelcase, no-var */
            var lookup_registration_code = $('#set_regcode_status_form input[name="regcode_code"]').val();
            /* eslint-disable-next-line camelcase, eqeqeq */
            if (lookup_registration_code == '') {
                // eslint-disable-next-line camelcase
                $registration_code_status_form_error.show();
                // eslint-disable-next-line camelcase
                $registration_code_status_form_error.text(gettext('Enter the enrollment code.'));
                // eslint-disable-next-line camelcase
                $lookup_button.removeAttr('disabled');
                return false;
            }
            $.ajax({
                type: 'GET',
                data: {
                    // eslint-disable-next-line camelcase
                    registration_code: lookup_registration_code
                },
                url: url,
                success: function(data) {
                    /* eslint-disable-next-line camelcase, no-var */
                    var is_registration_code_valid = data.is_registration_code_valid,
                        // eslint-disable-next-line camelcase
                        is_registration_code_redeemed = data.is_registration_code_redeemed,
                        // eslint-disable-next-line camelcase
                        is_registration_code_exists = data.is_registration_code_exists;

                    // eslint-disable-next-line camelcase
                    $lookup_button.removeAttr('disabled');
                    /* eslint-disable-next-line camelcase, eqeqeq */
                    if (is_registration_code_exists == 'false') {
                        // eslint-disable-next-line camelcase
                        $registration_code_status_form_error.hide();
                        // eslint-disable-next-line camelcase
                        $registration_code_status_form_error.show();
                        // eslint-disable-next-line camelcase
                        $registration_code_status_form_error.text(gettext(data.message));
                    } else {
                        /* eslint-disable-next-line camelcase, no-unused-vars, no-var */
                        var actions_links = '';
                        // eslint-disable-next-line no-var
                        var actions = [];
                        /* eslint-disable-next-line camelcase, eqeqeq */
                        if (is_registration_code_valid == true) {
                            actions.push(
                                {
                                    action_url: data.registration_code_detail_url,
                                    action_name: gettext('Cancel enrollment code'),
                                    // eslint-disable-next-line camelcase
                                    registration_code: lookup_registration_code,
                                    action_type: 'invalidate_registration_code'
                                }
                            );
                        } else {
                            actions.push(
                                {
                                    action_url: data.registration_code_detail_url,
                                    action_name: gettext('Restore enrollment code'),
                                    // eslint-disable-next-line camelcase
                                    registration_code: lookup_registration_code,
                                    action_type: 'validate_registration_code'
                                }
                            );
                        }
                        /* eslint-disable-next-line camelcase, eqeqeq */
                        if (is_registration_code_redeemed == true) {
                            actions.push(
                                {
                                    action_url: data.registration_code_detail_url,
                                    action_name: gettext('Mark enrollment code as unused'),
                                    // eslint-disable-next-line camelcase
                                    registration_code: lookup_registration_code,
                                    action_type: 'unredeem_registration_code'
                                }
                            );
                        }
                        // eslint-disable-next-line camelcase
                        is_registration_code_redeemed = is_registration_code_redeemed ? 'Yes' : 'No';
                        // eslint-disable-next-line camelcase
                        is_registration_code_valid = is_registration_code_valid ? 'Yes' : 'No';
                        // load the underscore template.
                        /* eslint-disable-next-line camelcase, no-var */
                        var template_data = _.template($('#enrollment-code-lookup-links-tpl').text());
                        /* eslint-disable-next-line camelcase, no-var */
                        var registration_code_lookup_actions = template_data(
                            {
                                // eslint-disable-next-line camelcase
                                lookup_registration_code: lookup_registration_code,
                                // eslint-disable-next-line camelcase
                                is_registration_code_redeemed: is_registration_code_redeemed,
                                // eslint-disable-next-line camelcase
                                is_registration_code_valid: is_registration_code_valid,
                                actions: actions
                            }
                        );

                        // before insertAfter do this.
                        // remove the first element after the registration_code_status_form
                        // so it doesn't duplicate the registration_code_lookup_actions in the UI.
                        // eslint-disable-next-line camelcase
                        $registration_code_status_form.next().remove();
                        edx.HtmlUtils.append($registration_code_status_form, $(registration_code_lookup_actions));
                    }
                },
                // eslint-disable-next-line no-unused-vars
                error: function(jqXHR, textStatus, errorThrown) {
                    // eslint-disable-next-line no-var
                    var data = $.parseJSON(jqXHR.responseText);
                    // eslint-disable-next-line camelcase
                    $lookup_button.removeAttr('disabled');
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.text(gettext(data.message));
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.show();
                }
            });
        });
        $('section#invalidate_registration_code_modal').on('click', 'a.registration_code_action_link', function(event) {
            event.preventDefault();
            // eslint-disable-next-line camelcase
            $registration_code_status_form_error.attr('style', 'display: none');
            // eslint-disable-next-line camelcase
            $lookup_button.attr('disabled', true);
            // eslint-disable-next-line no-var
            var url = $(this).data('endpoint');
            /* eslint-disable-next-line camelcase, no-var */
            var action_type = $(this).data('action-type');
            /* eslint-disable-next-line camelcase, no-var */
            var registration_code = $(this).data('registration-code');
            $.ajax({
                type: 'POST',
                data: {
                    // eslint-disable-next-line camelcase
                    registration_code: registration_code,
                    // eslint-disable-next-line camelcase
                    action_type: action_type
                },
                url: url,
                success: function(data) {
                    $('#set_regcode_status_form input[name="regcode_code"]').val('');
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form.next().remove();
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.hide();
                    // eslint-disable-next-line camelcase
                    $lookup_button.removeAttr('disabled');
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_success.text(gettext(data.message));
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_success.show();
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_success.fadeOut(3000);
                },
                // eslint-disable-next-line no-unused-vars
                error: function(jqXHR, textStatus, errorThrown) {
                    // eslint-disable-next-line no-var
                    var data = $.parseJSON(jqXHR.responseText);
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.hide();
                    // eslint-disable-next-line camelcase
                    $lookup_button.removeAttr('disabled');
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.show();
                    // eslint-disable-next-line camelcase
                    $registration_code_status_form_error.text(gettext(data.message));
                }
            });
        });
    });
// eslint-disable-next-line no-undef
}(Backbone, $, _, gettext));
