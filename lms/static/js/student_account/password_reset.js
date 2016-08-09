/**
 * Password reset template JS.
 */
$(function() {
    'use strict';
    // adding js class for styling with accessibility in mind
    $('body').addClass('js');

    // form field label styling on focus
    $('form :input').focus(function() {
        $("label[for='" + this.id + "']").parent().addClass('is-focused');
    }).blur(function() {
        $('label').parent().removeClass('is-focused');
    });
});
