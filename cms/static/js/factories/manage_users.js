define(['jquery', 'underscore', 'gettext', 'js/views/feedback_prompt'], function($, _, gettext, PromptView) {
    'use strict';
    return function (staffEmails, tplUserURL) {
        var unknownErrorMessage = gettext('Unknown'),
            $createUserForm = $('#create-user-form'),
            $createUserFormWrapper = $createUserForm.closest('.wrapper-create-user'),
            $cancelButton;

        $createUserForm.bind('submit', function(event) {
            event.preventDefault();
            var email = $('#user-email-input').val().trim(),
                url, msg;

            if(!email) {
                msg = new PromptView.Error({
                    title: gettext('A valid email address is required'),
                    message: gettext('You must enter a valid email address in order to add a new team member'),
                    actions: {
                        primary: {
                            text: gettext('Return and add email address'),
                            click: function(view) {
                                view.hide();
                                $('#user-email-input').focus();
                            }
                        }
                    }
                });
                msg.show();
            }

            if(_.contains(staffEmails, email)) {
                msg = new PromptView.Warning({
                    title: gettext('Already a course team member'),
                    message: _.template(
                        gettext("{email} is already on the “{course}” team. If you're trying to add a new member, please double-check the email address you provided."), {
                            email: email,
                            course: course.escape('name')
                        }, {interpolate: /\{(.+?)\}/g}
                    ),
                    actions: {
                        primary: {
                            text: gettext('Return to team listing'),
                            click: function(view) {
                                view.hide();
                                $('#user-email-input').focus();
                            }
                        }
                    }
                });
                msg.show();
            }

            url = tplUserURL.replace('@@EMAIL@@', $('#user-email-input').val().trim());
            $.ajax({
                url: url,
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                notifyOnError: false,
                data: JSON.stringify({role: 'staff'}),
                success: function(data) {location.reload();},
                error: function(jqXHR, textStatus, errorThrown) {
                    var message, prompt;
                    try {
                        message = JSON.parse(jqXHR.responseText).error || unknownErrorMessage;
                    } catch (e) {
                        message = unknownErrorMessage;
                    }
                    prompt = new PromptView.Error({
                        title: gettext('Error adding user'),
                        message: message,
                        actions: {
                            primary: {
                                text: gettext('OK'),
                                click: function(view) {
                                    view.hide();
                                    $('#user-email-input').focus();
                                }
                            }
                        }
                    });
                    prompt.show();
                }
            });
        });

        $cancelButton = $createUserForm.find('.action-cancel');
        $cancelButton.bind('click', function(event) {
            event.preventDefault();
            $('.create-user-button').toggleClass('is-disabled');
            $createUserFormWrapper.toggleClass('is-shown');
            $('#user-email-input').val('');
        });

        $('.create-user-button').bind('click', function(event) {
            event.preventDefault();
            $('.create-user-button').toggleClass('is-disabled');
            $createUserFormWrapper.toggleClass('is-shown');
            $createUserForm.find('#user-email-input').focus();
        });

        $('body').bind('keyup', function(event) {
            if(event.which == 27) {
                $cancelButton.click();
            }
        });

        $('.remove-user').click(function() {
            var email = $(this).data('id'),
                msg = new PromptView.Warning({
                    title: gettext('Are you sure?'),
                    message: _.template(gettext('Are you sure you want to delete {email} from the course team for “{course}”?'), {email: email, course: course.get('name')}, {interpolate: /\{(.+?)\}/g}),
                    actions: {
                        primary: {
                            text: gettext('Delete'),
                            click: function(view) {
                                var url = tplUserURL.replace('@@EMAIL@@', email);
                                view.hide();
                                $.ajax({
                                    url: url,
                                    type: 'DELETE',
                                    dataType: 'json',
                                    contentType: 'application/json',
                                    notifyOnError: false,
                                    success: function(data) {location.reload();},
                                    error: function(jqXHR, textStatus, errorThrown) {
                                        var message;
                                        try {
                                            message = JSON.parse(jqXHR.responseText).error || unknownErrorMessage;
                                        } catch (e) {
                                            message = unknownErrorMessage;
                                        }
                                        var prompt = new PromptView.Error({
                                            title: gettext('Error removing user'),
                                            message: message,
                                            actions: {
                                                primary: {
                                                    text: gettext('OK'),
                                                    click: function(view) {
                                                        view.hide();
                                                    }
                                                }
                                            }
                                        });
                                        prompt.show();
                                    }
                                });
                            }
                        },
                        secondary: {
                            text: gettext('Cancel'),
                            click: function(view) {
                                view.hide();
                            }
                        }
                    }
            });
            msg.show();
        });

        $('.toggle-admin-role').click(function(event) {
            event.preventDefault();
            var type, url, role;
            if($(this).hasClass('add-admin-role')) {
                role = 'instructor';
            } else {
                role = 'staff';
            }

            url = $(this).closest('li[data-url]').data('url');
            $.ajax({
                url: url,
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                notifyOnError: false,
                data: JSON.stringify({role: role}),
                success: function(data) {location.reload();},
                error: function(jqXHR, textStatus, errorThrown) {
                    var message, prompt;
                    try {
                        message = JSON.parse(jqXHR.responseText).error || unknownErrorMessage;
                    } catch (e) {
                        message = unknownErrorMessage;
                    }
                    prompt = new PromptView.Error({
                        title: gettext("There was an error changing the user's role"),
                        message: message,
                        actions: {
                            primary: {
                                text: gettext('Try Again'),
                                click: function(view) {
                                    view.hide();
                                }
                            }
                        }
                    });
                    prompt.show();
                }
            });
        });
    };
});
