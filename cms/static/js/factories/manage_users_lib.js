/*
    Code for editing users and assigning roles within a library context.
*/
define(['jquery', 'underscore', 'gettext', 'js/views/feedback_prompt', 'js/views/utils/view_utils'],
function($, _, gettext, PromptView, ViewUtils) {
    'use strict';
    return function (libraryName, allUserEmails, tplUserURL) {
        var unknownErrorMessage = gettext('Unknown'),
            $createUserForm = $('#create-user-form'),
            $createUserFormWrapper = $createUserForm.closest('.wrapper-create-user'),
            $cancelButton;

        // Our helper method that calls the RESTful API to add/remove/change user roles:
        var changeRole = function(email, newRole, opts) {
            var url = tplUserURL.replace('@@EMAIL@@', email);
            var errMessage = opts.errMessage || gettext("There was an error changing the user's role");
            var onSuccess = opts.onSuccess || function(data){ ViewUtils.reload(); };
            var onError = opts.onError || function(){};
            $.ajax({
                url: url,
                type: newRole ? 'POST' : 'DELETE',
                dataType: 'json',
                contentType: 'application/json',
                notifyOnError: false,
                data: JSON.stringify({role: newRole}),
                success: onSuccess,
                error: function(jqXHR, textStatus, errorThrown) {
                    var message, prompt;
                    try {
                        message = JSON.parse(jqXHR.responseText).error || unknownErrorMessage;
                    } catch (e) {
                        message = unknownErrorMessage;
                    }
                    prompt = new PromptView.Error({
                        title: errMessage,
                        message: message,
                        actions: {
                            primary: { text: gettext('OK'), click: function(view) { view.hide(); onError(); } }
                        }
                    });
                    prompt.show();
                }
            });
        };

        $createUserForm.bind('submit', function(event) {
            event.preventDefault();
            var email = $('#user-email-input').val().trim();
            var msg;

            if(!email) {
                msg = new PromptView.Error({
                    title: gettext('A valid email address is required'),
                    message: gettext('You must enter a valid email address in order to add an instructor'),
                    actions: {
                        primary: {
                            text: gettext('Return and add email address'),
                            click: function(view) { view.hide(); $('#user-email-input').focus(); }
                        }
                    }
                });
                msg.show();
                return;
            }

            if(_.contains(allUserEmails, email)) {
                msg = new PromptView.Warning({
                    title: gettext('Already a library team member'),
                    message: _.template(
                        gettext("{email} is already on the {course} team. Recheck the email address if you want to add a new member."), {
                            email: email,
                            course: libraryName
                        }, {interpolate: /\{(.+?)\}/g}
                    ),
                    actions: {
                        primary: {
                            text: gettext('Return to team listing'),
                            click: function(view) { view.hide(); $('#user-email-input').focus(); }
                        }
                    }
                });
                msg.show();
                return;
            }

            // Use the REST API to create the user, giving them a role of "library_user" for now:
            changeRole(
                $('#user-email-input').val().trim(),
                'library_user',
                {
                    errMessage: gettext('Error adding user'),
                    onError: function() { $('#user-email-input').focus(); }
                }
            );
        });

        $cancelButton = $createUserForm.find('.action-cancel');
        $cancelButton.on('click', function(event) {
            event.preventDefault();
            $('.create-user-button').toggleClass('is-disabled');
            $createUserFormWrapper.toggleClass('is-shown');
            $('#user-email-input').val('');
        });

        $('.create-user-button').on('click', function(event) {
            event.preventDefault();
            $('.create-user-button').toggleClass('is-disabled');
            $createUserFormWrapper.toggleClass('is-shown');
            $createUserForm.find('#user-email-input').focus();
        });

        $('body').on('keyup', function(event) {
            if(event.which == jQuery.ui.keyCode.ESCAPE && $createUserFormWrapper.is('.is-shown')) {
                $cancelButton.click();
            }
        });

        $('.remove-user').click(function() {
            var email = $(this).closest('li[data-email]').data('email'),
                msg = new PromptView.Warning({
                    title: gettext('Are you sure?'),
                    message: _.template(gettext('Are you sure you want to delete {email} from the library “{library}”?'), {email: email, library: libraryName}, {interpolate: /\{(.+?)\}/g}),
                    actions: {
                        primary: {
                            text: gettext('Delete'),
                            click: function(view) {
                                // User the REST API to delete the user:
                                changeRole(email, null, { errMessage: gettext('Error removing user') });
                            }
                        },
                        secondary: {
                            text: gettext('Cancel'),
                            click: function(view) { view.hide(); }
                        }
                    }
            });
            msg.show();
        });

        $('.user-actions .make-instructor').click(function(event) {
            event.preventDefault();
            var email = $(this).closest('li[data-email]').data('email');
            changeRole(email, 'instructor', {});
        });

        $('.user-actions .make-staff').click(function(event) {
            event.preventDefault();
            var email = $(this).closest('li[data-email]').data('email');
            changeRole(email, 'staff', {});
        });

        $('.user-actions .make-user').click(function(event) {
            event.preventDefault();
            var email = $(this).closest('li[data-email]').data('email');
            changeRole(email, 'library_user', {});
        });

    };
});
