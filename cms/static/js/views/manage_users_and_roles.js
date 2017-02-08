/*
 Code for editing users and assigning roles within a course or library team context.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/baseview',
        'common/js/components/views/feedback_prompt', 'common/js/components/utils/view_utils'],
    function($, _, gettext, BaseView, PromptView, ViewUtils) {
        'use strict';
        var default_messages = {
            defaults: {
                confirmation: gettext('Ok'),
                changeRoleError: gettext("There was an error changing the user's role"),
                unknown: gettext('Unknown')
            },
            errors: {
                addUser: gettext('Error adding user'),
                deleteUser: gettext('Error removing user')
            },
            invalidEmail: {
                title: gettext('A valid email address is required'),
                message: gettext('You must enter a valid email address in order to add a new team member'),
                primaryAction: gettext('Return and add email address')
            },
            alreadyMember: {
                title: gettext('Already a member'),
                messageTpl: gettext('{email} is already on the {container} team. Recheck the email address if you want to add a new member.'),
                primaryAction: gettext('Return to team listing')
            },
            deleteUser: {
                title: gettext('Are you sure?'),
                messageTpl: gettext('Are you sure you want to restrict {email} access to “{container}”?'),
                primaryAction: gettext('Delete'),
                secondaryAction: gettext('Cancel')
            }
        };

        function makeInvalidEmailMessage(messages) {
            return new PromptView.Error({
                title: messages.invalidEmail.title,
                message: messages.invalidEmail.message,
                actions: {
                    primary: {
                        text: messages.invalidEmail.primaryAction,
                        click: function(view) {
                            view.hide();
                            $('#user-email-input').focus();
                        }
                    }
                }
            });
        }

        function makeAlreadyMemberMessage(messages, email, containerName) {
            return new PromptView.Warning({
                title: messages.alreadyMember.title,
                message: _.template(
                    messages.alreadyMember.messageTpl,
                    {interpolate: /\{(.+?)}/g})(
                    {email: email, container: containerName}
                ),
                actions: {
                    primary: {
                        text: messages.alreadyMember.primaryAction,
                        click: function(view) {
                            view.hide();
                            $('#user-email-input').focus();
                        }
                    }
                }
            });
        }

        function makeChangeRoleErrorMessage(messages, title, message, onErrorCallback) {
            return new PromptView.Error({
                title: title,
                message: message,
                actions: {
                    primary: {
                        text: messages.defaults.confirmation,
                        click: function(view) {
                            view.hide();
                            onErrorCallback();
                        }
                    }
                }
            });
        }

        function getEmail(button) {
            return $(button).closest('li[data-email]').data('email');
        }

        var ManageUsersAndRoles = BaseView.extend({
            events: function() {
                var baseEvents = {
                    'click .create-user-button': 'addUserHandler',
                    'submit #create-user-form': 'createUserFormSubmit',
                    'click .action-cancel': 'cancelEditHandler',
                    'keyup': 'keyUpHandler',
                    'click .remove-user': 'removeUserHandler'
                };
                var roleEvents = {};
                var self = this;
                for (var i = 0; i < self.options.roles.length; i++) {
                    var role_name = self.options.roles[i].key;
                    var role_selector = 'click .user-actions .make-' + role_name;

                    (function(role) {
                        roleEvents[role_selector] = function(event) { self.handleRoleButtonClick(event.target, role); };
                    })(role_name);
                }
                return _.extend(baseEvents, roleEvents);
            },

            initialize: function(options) {
                BaseView.prototype.initialize.call(this);
                this.containerName = options.containerName;
                this.tplUserURL = options.tplUserURL;

                this.roles = options.roles; // [{key:role_key, name:Human-readable Name}, {key: admin, name: Admin}]
                this.users = options.users; // [{username: username, email: email, role: role}, ...]
                this.allow_actions = options.allow_actions;
                this.current_user_id = options.current_user_id;

                this.initial_role = this.roles[0];
                this.admin_role = this.roles[this.roles.length - 1];

                var message_mod = options.messages_modifier || function(messages) { return messages; };
                this.messages = message_mod(default_messages);

                this.$userEmailInput = this.$el.find('#user-email-input');
                this.$createUserButton = this.$el.find('.create-user-button');
                this.$createUserFormWrapper = this.$el.find('.wrapper-create-user');
                this.$cancelButton = this.$el.find('.action-cancel');
                this.$userList = this.$el.find('#user-list');
            },

            render: function() {
                this.$userList.empty();
                var templateFn = this.loadTemplate('team-member'),
                    roles = _.object(_.pluck(this.roles, 'key'), _.pluck(this.roles, 'name')),
                    adminRoleCount = this.getAdminRoleCount(),
                    viewHelpers = {
                        format: function(template, data) {
                            return _.template(template, {interpolate: /\{(.+?)}/g})(data);
                        }
                    };
                for (var i = 0; i < this.users.length; i++) {
                    var user = this.users[i],
                        is_current_user = this.current_user_id == user.id;
                    var template_data = {
                        user: user,
                        actions: this.getPossibleRoleChangesForRole(user.role, adminRoleCount),
                        roles: roles,
                        allow_delete: !(user.role === this.admin_role.key && adminRoleCount === 1),
                        allow_actions: this.allow_actions,
                        is_current_user: is_current_user,
                        viewHelpers: viewHelpers
                    };

                    this.$userList.append(templateFn(template_data));
                }
            },

            getAdminRoleCount: function() {
                var self = this;
                return _.filter(this.users, function(user) { return user.role === self.admin_role.key; }).length;
            },

            getPossibleRoleChangesForRole: function(role, adminRoleCount) {
                var result = [],
                    role_names = _.map(this.roles, function(role) { return role.key; });
                if (role === this.admin_role.key && adminRoleCount === 1) {
                    result.push({notoggle: true});
                }
                else {
                    var currentRoleIdx = _.indexOf(role_names, role);
                    // in reverse order to show "Add" buttons to the left, "Remove" to the right
                    for (var i = this.roles.length - 1; i >= 0; i--) {
                        var other_role = this.roles[i];
                        if (Math.abs(currentRoleIdx - i) !== 1) continue; // allows moving only to adjacent roles
                        result.push({
                            to_role: other_role.key,
                            label: (i < currentRoleIdx) ? this.roles[currentRoleIdx].name : other_role.name,
                            direction: (i < currentRoleIdx) ? 'remove' : 'add'
                        });
                    }
                }
                return result;
            },

            checkEmail: function(email) {
                var allUsersEmails = _.map(this.users, function(user) { return user.email; });

                if (!email) {
                    return {valid: false, msg: makeInvalidEmailMessage(this.messages)};
                }

                if (_.contains(allUsersEmails, email)) {
                    return {valid: false, msg: makeAlreadyMemberMessage(this.messages, email, this.containerName)};
                }
                return {valid: true};
            },

            // Our helper method that calls the RESTful API to add/remove/change user roles:
            changeRole: function(email, newRole, opts) {
                var self = this;
                var url = this.tplUserURL.replace('@@EMAIL@@', email);
                var errMessage = opts.errMessage || this.messages.defaults.changeRoleError;
                var onSuccess = opts.onSuccess || function(data) { ViewUtils.reload(); };
                var onError = opts.onError || function() {};
                $.ajax({
                    url: url,
                    type: newRole ? 'POST' : 'DELETE',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({role: newRole}),
                    success: onSuccess,
                    error: function(jqXHR, textStatus, errorThrown) {
                        var message, prompt;
                        try {
                            message = JSON.parse(jqXHR.responseText).error || self.messages.defaults.unknown;
                        } catch (e) {
                            message = self.messages.defaults.unknown;
                        }
                        prompt = makeChangeRoleErrorMessage(self.messages, errMessage, message, onError);
                        prompt.show();
                    }
                });
            },

            handleRoleButtonClick: function(button, role) {
                this.changeRole(getEmail(button), role, {});
            },

            addUserHandler: function(event) {
                event.preventDefault();
                this.$createUserButton
                    .toggleClass('is-disabled')
                    .attr('aria-disabled', this.$createUserButton.hasClass('is-disabled'));
                this.$createUserFormWrapper.toggleClass('is-shown');
                this.$userEmailInput.focus();
            },

            cancelEditHandler: function(event) {
                event.preventDefault();
                this.$createUserButton
                    .toggleClass('is-disabled')
                    .attr('aria-disabled', this.$createUserButton.hasClass('is-disabled'));
                this.$createUserFormWrapper.toggleClass('is-shown');
                this.$userEmailInput.val('');
            },

            createUserFormSubmit: function(event) {
                event.preventDefault();
                var self = this;
                var email = this.$userEmailInput.val().trim();
                var emailCheck = this.checkEmail(email);

                if (!emailCheck.valid) {
                    emailCheck.msg.show();
                    return;
                }

                // Use the REST API to create the user, assigning them initial role for now:
                this.changeRole(
                    email,
                    this.initial_role.key,
                    {
                        errMessage: this.messages.errors.addUser,
                        onError: function() { self.$userEmailInput.focus(); }
                    }
                );
            },

            keyUpHandler: function(event) {
                if (event.which === jQuery.ui.keyCode.ESCAPE && this.$createUserFormWrapper.is('.is-shown')) {
                    this.$cancelButton.click();
                }
            },

            removeUserHandler: function(event) {
                event.preventDefault();
                var self = this;
                var email = getEmail(event.target);
                var msg = new PromptView.Warning({
                    title: self.messages.deleteUser.title,
                    message: _.template(
                        self.messages.deleteUser.messageTpl,
                        {interpolate: /\{(.+?)}/g})(
                        {email: email, container: self.containerName}
                    ),
                    actions: {
                        primary: {
                            text: self.messages.deleteUser.primaryAction,
                            click: function(view) {
                                view.hide();
                                // Use the REST API to delete the user:
                                self.changeRole(email, null, {errMessage: self.messages.errors.deleteUser});
                            }
                        },
                        secondary: {
                            text: self.messages.deleteUser.secondaryAction,
                            click: function(view) { view.hide(); }
                        }
                    }
                });
                msg.show();
            }
        });

        return ManageUsersAndRoles;
    });
