// eslint-disable-next-line no-undef
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

        // eslint-disable-next-line no-var
        var reloadPage = function() {
            // eslint-disable-next-line no-restricted-globals
            location.reload();
        };

        // eslint-disable-next-line no-var
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

        // eslint-disable-next-line no-unused-vars
        $('#request-coursecreator-submit').click(function(event) {
            $(this)
                .toggleClass('is-disabled is-submitting')
                .attr('aria-disabled', $(this).hasClass('is-disabled'))
                .find('.label')
                .text('Submitting Your Request');
        });
    };
});
