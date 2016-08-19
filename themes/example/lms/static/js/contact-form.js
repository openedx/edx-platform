(function(require) {
    'use strict';

    require(['edx-ui-toolkit/js/utils/html-utils', 'edx-ui-toolkit/js/utils/string-utils'],
        function(HtmlUtils, StringUtils) {
            var errorMessages = {
                name: 'Please provide your name.',
                email: 'Please provide a valid e-mail.',
                details: 'Please provide message.',
                subject: 'Please provide an inquiry type.'
            };
            function addErrorDiv(id) {
                var start = HtmlUtils.HTML('<div class="has-error field-message"><span class="field-message-content">'),
                    errorDiv = StringUtils.interpolate(
                    '{start}{errorMessage}{end}',
                        {
                            start: start,
                            errorMessage: errorMessages[id],
                            end: HtmlUtils.HTML('</span></div>')
                        }
                );
                $('#' + id).addClass('has-error');
                $('#' + id).parent().append(HtmlUtils.template(errorDiv)().toString());
            }
            function submitForm(data) {
                $.post('/submit_feedback', data, function() {
                    $('#success-message-btn').click();
                    setTimeout(function() {
                        $('#lean_overlay').trigger('click');
                        $('#contact_form').trigger('reset');
                    }, 2000);
                }).fail(function(xhr) {
                    var responseData = jQuery.parseJSON(xhr.responseText);
                    addErrorDiv(responseData.field);
                });
            }

            function removeErrorDiv(id) {
                $('#' + id).removeClass('has-error');
                $($('#' + id).next()).remove();
            }
            function validateForm() {
                var optionalFields = ['user_type']; // Optional fields array
                var formValues = $('#contact_form').find(':input'),
                    i = 0,
                    data = {},
                    value = '',
                    id = '',
                    response = {
                        is_form_validate: true,
                        data: ''
                    };

                for (i = 0; i < formValues.length - 2; i++) {
                    value = $(formValues[i]).val();
                    id = $(formValues[i]).attr('id');
                    removeErrorDiv(id);

                    if (value && value !== '') {
                        data[id] = value;
                    } else {
                        if ($.inArray(id, optionalFields) === -1) {
                            response.is_form_validate = false;
                            addErrorDiv(id);
                        }
                    }
                }
                response.data = data;
                return response;
            }
            $(function() {
                var validateFormData = '';
                $('#submit_btn').click(function(e) {
                    e.preventDefault();
                    validateFormData = validateForm();
                    if (validateFormData.is_form_validate) {
                        submitForm(validateFormData.data);
                    }
                });
            });
        });
}).call(this, require || RequireJS.require);
