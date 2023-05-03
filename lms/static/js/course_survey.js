$(function() {
    // adding js class for styling with accessibility in mind
    $('body').addClass('js');

    // form field label styling on focus
    $('form :input').focus(function() {
        $("label[for='" + this.id + "']").parent().addClass('is-focused');
    }).blur(function() {
        $('label').parent().removeClass('is-focused');
    });

    $('.status.message.submission-error').addClass('is-hidden');

    toggleSubmitButton(true);

    $('#survey-form').on('submit', function() {
        /* validate required fields */

        var $inputs = $('#survey-form :input');

        $('.status.message.submission-error .message-copy').empty();

        var cancel_submit = false;

        $inputs.each(function() {
            var val, fieldLabel;
            /* see if it is a required field and - if so - make sure user presented all information */
            if (typeof $(this).attr('required') !== typeof undefined) {
                val = $(this).val();
                if (typeof(val) === 'string') {
                    if (val.trim().length === 0) {
                        fieldLabel = $(this).parent().find('label');
                        $(this).parent().addClass('field-error');
                        // eslint-disable-next-line max-len
                        $('.status.message.submission-error .message-copy').append(edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML("<li class='error-item'>"), fieldLabel.text(), edx.HtmlUtils.HTML('</li>')).toString());
                        cancel_submit = true;
                    }
                } else if (typeof(val) === 'object') {
                    /* for SELECT statements */
                    if (val === null || val.length === 0 || val[0] === '') {
                        fieldLabel = $(this).parent().find('label');
                        $(this).parent().addClass('field-error');
                        // eslint-disable-next-line max-len
                        $('.status.message.submission-error .message-copy').append(edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML("<li class='error-item'>"), fieldLabel.text(), edx.HtmlUtils.HTML('</li>')).toString());
                        cancel_submit = true;
                    }
                }
            }
        });

        if (cancel_submit) {
            $('.status.message.submission-error').
                removeClass('is-hidden').
                focus();
            $('html, body').animate({scrollTop: 0}, 'fast');
            return false;
        }

        toggleSubmitButton(false);
    });

    $('#survey-form').on('ajax:error', function() {
        toggleSubmitButton(true);
    });

    $('#survey-form').on('ajax:success', function(event, json, xhr) {
        var url = json.redirect_url;
        location.href = url;
    });

    $('#survey-form').on('ajax:error', function(event, jqXHR, textStatus) {
        toggleSubmitButton(true);
        json = $.parseJSON(jqXHR.responseText);
        $('.status.message.submission-error').addClass('is-shown').focus();
        $('.status.message.submission-error .message-copy').
            text(gettext('There has been an error processing your survey.')).
            stop().
            css('display', 'block');
    });
});

function toggleSubmitButton(enable) {
    var $submitButton = $('form .form-actions #submit');

    if (enable) {
        $submitButton.
            removeClass('is-disabled').
            attr('aria-disabled', false).
            removeProp('disabled');
    } else {
        $submitButton.
            addClass('is-disabled').
            attr('aria-disabled', true).
            prop('disabled', true);
    }
}
