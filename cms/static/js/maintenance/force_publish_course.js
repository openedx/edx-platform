define([ // jshint ignore:line
    'jquery',
    'underscore',
    'gettext',
    'common/js/components/utils/view_utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'edx-ui-toolkit/js/utils/html-utils'
],
function($, _, gettext, ViewUtils, StringUtils, HtmlUtils) {
    'use strict';
    return function(maintenanceViewURL) {
        var showError;
        // Reset values
        $('#reset-button').click(function(e) {
            e.preventDefault();
            $('#course-id').val('');
            $('#dry-run').prop('checked', true);
            // clear out result container
            $('#result-container').html('');
        });

        showError = function(containerElSelector, error) {
            var errorWrapperElSelector, errorHtml;
            errorWrapperElSelector = containerElSelector + ' .wrapper-error';
            errorHtml = HtmlUtils.joinHtml(
                HtmlUtils.HTML('<div class="error" aria-live="polite" id="course-id-error">'),
                error,
                HtmlUtils.HTML('</div>')
            );
            HtmlUtils.setHtml($(errorWrapperElSelector), HtmlUtils.HTML(errorHtml));
            $(errorWrapperElSelector).css('display', 'inline-block');
            $(errorWrapperElSelector).fadeOut(5000);
        };

        $('form#force_publish').submit(function(event) {
            var attrs, forcePublishedTemplate, $submitButton, deferred, promise, data;
            event.preventDefault();

            // clear out result container
            $('#result-container').html('');

            $submitButton = $('#submit_force_publish');
            deferred = new $.Deferred();
            promise = deferred.promise();

            data = $('#force_publish').serialize();

            // disable submit button while executing.
            ViewUtils.disableElementWhileRunning($submitButton, function() { return promise; });

            $.ajax({
                type: 'POST',
                url: maintenanceViewURL,
                dataType: 'json',
                data: data
            })
                .done(function(response) {
                    if (response.error) {
                        showError('#course-id-container', response.msg);
                    } else {
                        if (response.msg) {
                            showError('#result-error', response.msg);
                        } else {
                            attrs = $.extend({}, response, {StringUtils: StringUtils});
                            forcePublishedTemplate = HtmlUtils.template(
                                $('#force-published-course-response-tpl').text()
                            );
                            HtmlUtils.setHtml($('#result-container'), forcePublishedTemplate(attrs));
                        }
                    }
                })
                .fail(function() {
                // response.responseText here because it would show some strange output, it may output Traceback
                // sometimes if unexpected issue arises. Better to show just internal error when getting 500 error.
                    showError('#result-error', gettext('Internal Server Error.'));
                })
                .always(function() {
                    deferred.resolve();
                });
        });
    };
});

