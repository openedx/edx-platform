define([ // jshint ignore:line
    'jquery',
    'underscore',
    'gettext',
    'common/js/components/utils/view_utils',
    'edx-ui-toolkit/js/utils/string-utils',
    "edx-ui-toolkit/js/utils/html-utils",
    'text!templates/maintenance/force-published-course-response.underscore'
],
function($, _, gettext, ViewUtils, StringUtils, HtmlUtils, ForcePublishedTemplate) {
    'use strict';
    return function (maintenanceViewURL) {

        // Reset values
        $('#reset-button').click(function (e) {
            e.preventDefault();
            $('#course-id').val('');
            $('#dry-run').prop('checked', true);
            // clear out result container
            $('#result-container').html('');
        });

        var showError = function(containerElSelector, error){
            var errorWrapperElSelector = containerElSelector + ' .wrapper-error';
            var errorHtml = '<div class="error" aria-live="polite" id="course-id-error">' + error + '</div>';
            HtmlUtils.setHtml(
                $(errorWrapperElSelector),
                HtmlUtils.HTML(errorHtml)
            );
            $(errorWrapperElSelector).css('display', 'inline-block');
            $(errorWrapperElSelector).fadeOut(5000);
        };

        $('form#force_publish').submit(function(event) {

            event.preventDefault();

            // clear out result container
            $('#result-container').html('');

            var submitButton = $('#submit_force_publish'),
                deferred = new $.Deferred(),
                promise = deferred.promise();
            ViewUtils.disableElementWhileRunning(submitButton, function() { return promise; });

            var data = $('#force_publish').serialize();

            $.ajax({
                type:'POST',
                url: maintenanceViewURL,
                dataType: 'json',
                data: data,
            })
            .done(function(response) {
                if(response.error){
                    showError('#course-id-container', response.msg);
                }
                else {
                    if(response.msg) {
                        showError('#result-error', response.msg);
                    }
                    else{
                        var attrs = $.extend({}, response, {StringUtils: StringUtils});
                        HtmlUtils.setHtml(
                            $('#result-container'),
                            HtmlUtils.template(ForcePublishedTemplate)(attrs)
                        );
                    }
                }
            })
            .fail(function(response) {  // jshint ignore:line
                // response.responseText here because it would show some strange output, it may output Traceback
                // sometimes if unexpected issue arises. Better to show just internal error when getting 500 error.
                showError('#result-error', gettext('Internal Server Error.'));
            })
            .always(function(response) { // jshint ignore:line
                deferred.resolve();
            });
        });
    };
});

