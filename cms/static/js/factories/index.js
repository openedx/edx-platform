define(['jquery.form', 'js/index'], function() {
    'use strict';
    return function() {
        // showing/hiding creation rights UI
        $('.show-creationrights').click(function(e) {
            e.preventDefault();
            $(this)
                .closest('.wrapper-creationrights')
                    .toggleClass('is-shown')
                .find('.ui-toggle-control')
                    .toggleClass('current');
        });

        var reloadPage = function() {
            location.reload();
        };

        var showError = function() {
            $('#request-coursecreator-submit')
                .toggleClass('has-error')
                .find('.label')
                    .text('Sorry, there was error with your request');
            $('#request-coursecreator-submit')
                .find('.fa-cog')
                    .toggleClass('fa-spin');
        };

        $('#request-coursecreator').ajaxForm({
            error: showError,
            success: reloadPage
        });

        $('#request-coursecreator-submit').click(function(event) {
            $(this)
                .toggleClass('is-disabled is-submitting')
                .attr('aria-disabled', $(this).hasClass('is-disabled'))
                .find('.label')
                .text('Submitting Your Request');
        });
    };
});
